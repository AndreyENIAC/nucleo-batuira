function agendar(){
    const nome = document.getElementById('nome').value;
    const data = document.getElementById('data').value;
    const hora = document.getElementById('hora').value;

    if(!nome || !data || !hora){
        alert("Preencha todos os campos")
        return;
    }

    const lista = document.getElementById('listaAgendamentos');
    const item = document.createElement('p');
    item.textContent = `${nome} foi agendado para ${data} ás ${hora}`;
    lista.appendChild(item)

    document.getElementById('nome').value = '';
    document.getElementById('data').value = '';
    document.getElementById('hora').value = '';


    document.getElementById('meuFormulario').addEventListener ('submit'), function(event) {
        event.preventDefault();
}
    const nomeDigitado = document.getElementById(item).value;

    localStorage.setItem('usuarioNome', nomeDigitado);

    const nomeSalvo = localStorage.getItem('usuarioNome');

    if (nomeSalvo) {
        document.getElementById('resultadoNome').textContent = nomeSalvo;
    }

}

const tabs = document.querySelectorAll('.tab-btn');

tabs.forEach(tab => tab.addEventListener('click', () => tabClicked(tab)));

const tabClicked = (tab) => {
    tabs.forEach(tab => tab.classList.remove('active'));
    tab.classList.add('active');

    const contents = document.querySelectorAll('.content');
    contents.forEach(content => content.classList.remove('show'));

    const contentId = tab.getAttribute('content-id');

    const content = document.getElementById(contentId);

    content.classList.add('show');
}

const currentActiveTab = document.querySelector('.tab-btn-active');
tabClicked(currentActiveTab);