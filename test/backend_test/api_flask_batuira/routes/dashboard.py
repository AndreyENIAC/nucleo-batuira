from __future__ import annotations

from datetime import date, datetime, timedelta

from flask import Blueprint, g

from database import fetch_all, fetch_one
from responses import success
from security import auth_required

bp = Blueprint("dashboard", __name__)


def scalar(sql:str,params=()):
    row=fetch_one(sql,params)
    return next(iter(row.values())) if row else 0


@bp.get("/dashboard")
@auth_required("admin", "technical", "financial", "staff")
def dashboard():
    user=g.current_user;role=user["perfil_codigo"];today=date.today().isoformat();month=today[:7]
    common={
        "acolhidos_ativos":scalar("SELECT COUNT(*) total FROM acolhidos WHERE status!='inativo'"),
        "acolhidos_criticos":scalar("SELECT COUNT(*) total FROM acolhidos WHERE status='critico'"),
        "alertas_abertos":scalar("SELECT COUNT(*) total FROM alertas WHERE status IN ('aberto','em_tratamento')"),
    }
    agenda=fetch_all("""SELECT e.id,e.titulo,e.tipo,e.inicio,e.fim,e.local,a.nome AS acolhido_nome
    FROM eventos_agenda e LEFT JOIN acolhidos a ON a.id=e.acolhido_id
    WHERE substr(e.inicio,1,10)=? ORDER BY e.inicio LIMIT 10""",(today,))
    data={"perfil":role,"usuario":{"id":user["id"],"nome":user["nome"]},"resumo":common,"agenda_hoje":agenda}

    if role=="admin":
        common.update({
            "usuarios_ativos":scalar("SELECT COUNT(*) total FROM usuarios WHERE ativo=1"),
            "receitas_mes":scalar("SELECT COALESCE(SUM(valor),0) total FROM receitas WHERE substr(data_recebimento,1,7)=?",(month,)),
            "gastos_mes":scalar("SELECT COALESCE(SUM(valor),0) total FROM gastos WHERE substr(data_gasto,1,7)=?",(month,)),
            "documentos_vencendo":scalar("SELECT COUNT(*) total FROM documentos WHERE data_validade IS NOT NULL AND date(data_validade) BETWEEN date(?) AND date(?)",(today,(date.today()+timedelta(days=30)).isoformat())),
        })
    elif role=="technical":
        common.update({
            "prescricoes_ativas":scalar("SELECT COUNT(*) total FROM prescricoes WHERE status='ativa'"),
            "medicacoes_pendentes_hoje":scalar("SELECT COUNT(*) total FROM administracoes_medicamentos WHERE substr(previsto_para,1,10)=? AND status='pendente'",(today,)),
            "consultas_hoje":scalar("SELECT COUNT(*) total FROM eventos_agenda WHERE substr(inicio,1,10)=? AND lower(tipo) IN ('médica','medica','consulta','reabilitação','reabilitacao')",(today,)),
        })
        data["alertas_recentes"]=fetch_all("""SELECT a.*,ac.nome AS acolhido_nome FROM alertas a
        LEFT JOIN acolhidos ac ON ac.id=a.acolhido_id WHERE a.status IN ('aberto','em_tratamento')
        ORDER BY CASE a.severidade WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 ELSE 3 END,a.criado_em DESC LIMIT 10""")
    elif role=="financial":
        revenue=scalar("SELECT COALESCE(SUM(valor),0) total FROM receitas WHERE substr(data_recebimento,1,7)=?",(month,))
        expense=scalar("SELECT COALESCE(SUM(valor),0) total FROM gastos WHERE substr(data_gasto,1,7)=?",(month,))
        common.update({"receitas_mes":revenue,"gastos_mes":expense,"saldo_mes":revenue-expense,
                       "prestacoes_pendentes":scalar("SELECT COUNT(*) total FROM prestacoes_contas WHERE status IN ('rascunho','em_analise')"),
                       "recursos_em_atencao":scalar("SELECT COUNT(*) total FROM recursos_administrativos WHERE status IN ('atencao','vencido')")})
        data["gastos_recentes"]=fetch_all("""SELECT g.id,g.descricao,g.valor,g.data_gasto,a.nome AS acolhido_nome
        FROM gastos g LEFT JOIN acolhidos a ON a.id=g.acolhido_id ORDER BY g.data_gasto DESC,g.id DESC LIMIT 5""")
    elif role=="staff":
        uid=user["id"]
        common.update({
            "tarefas_pendentes":scalar("SELECT COUNT(*) total FROM tarefas WHERE responsavel_id=? AND status IN ('pendente','em_andamento')",(uid,)),
            "tarefas_concluidas":scalar("SELECT COUNT(*) total FROM tarefas WHERE responsavel_id=? AND status='concluida'",(uid,)),
            "tarefas_hoje":scalar("SELECT COUNT(*) total FROM tarefas WHERE responsavel_id=? AND substr(prazo,1,10)=?",(uid,today)),
        })
        data["tarefas"]=fetch_all("""SELECT * FROM tarefas WHERE responsavel_id=? AND status IN ('pendente','em_andamento')
        ORDER BY prazo LIMIT 10""",(uid,))
    return success(data)
