// Filtros, ordem e busca das listas. Sem esta parte a página continua inteira, só não filtra.
(function () {
  function norm(t) { return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }

  function ativar(grupo, atributo, valor) {
    grupo.querySelectorAll("button[" + atributo + "]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute(atributo) === valor));
    });
  }

  document.querySelectorAll("[data-filtravel]").forEach(function (lista) {
    var busca = lista.querySelector("input");
    var itens = Array.prototype.slice.call(lista.querySelectorAll(".pessoa"));
    var contagem = lista.querySelector(".contagem");
    var estado = { tipo: "", ordem: "nome" };
    var alvo = lista.querySelector(".itens");

    function chave(i, ordem) {
      if (ordem === "votos") { return -Number(i.dataset.votos); }
      return norm(ordem === "partido" ? i.dataset.partido + " " + i.dataset.nome : i.dataset.nome);
    }

    function aplicar() {
      var termo = norm(busca.value.trim());
      var visiveis = 0;
      itens.sort(function (a, b) {
        var x = chave(a, estado.ordem), y = chave(b, estado.ordem);
        return x < y ? -1 : x > y ? 1 : 0;
      });
      itens.forEach(function (i) {
        var ok = (!estado.tipo || i.dataset.tipo === estado.tipo) &&
          (!termo || norm(i.dataset.nome).indexOf(termo) >= 0 || norm(i.dataset.partido).indexOf(termo) >= 0);
        i.hidden = !ok;
        if (ok) { visiveis += 1; }
        alvo.appendChild(i);
      });
      contagem.textContent = visiveis === 0 ? "Ninguém encontrado. Tente outro nome ou volte para Todos."
        : "Mostrando " + visiveis + " de " + itens.length;
    }

    busca.addEventListener("input", aplicar);
    lista.querySelectorAll("button[data-tipo]").forEach(function (b) {
      b.addEventListener("click", function () { estado.tipo = b.dataset.tipo; ativar(lista, "data-tipo", estado.tipo); aplicar(); });
    });
    lista.querySelectorAll("button[data-ordem]").forEach(function (b) {
      b.addEventListener("click", function () { estado.ordem = b.dataset.ordem; ativar(lista, "data-ordem", estado.ordem); aplicar(); });
    });
    aplicar();
  });

  var estados = document.getElementById("estados");
  if (estados) {
    var campo = document.getElementById("busca-estado");
    var regiao = "Todas";
    var filtrar = function () {
      var termo = norm(campo.value.trim());
      estados.querySelectorAll("li").forEach(function (li) {
        li.hidden = !((regiao === "Todas" || li.dataset.regiao === regiao) && (!termo || norm(li.dataset.nome).indexOf(termo) >= 0));
      });
    };
    campo.addEventListener("input", filtrar);
    document.querySelectorAll("button[data-regiao]").forEach(function (b) {
      b.addEventListener("click", function () { regiao = b.dataset.regiao; ativar(b.parentNode, "data-regiao", regiao); filtrar(); });
    });
  }
})();
