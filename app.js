// Filtros, ordem e busca das listas. Sem esta parte a página continua inteira, só não filtra.
(function () {
  function norm(t) { return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }

  document.querySelectorAll("[data-filtravel]").forEach(function (lista) {
    var busca = lista.querySelector("input");
    var itens = Array.prototype.slice.call(lista.querySelectorAll(".pessoa"));
    var contagem = lista.querySelector(".contagem");
    var estado = { tipo: "", cargo: "", grupo: "", ordem: "nome" };
    var alvo = lista.querySelector(".itens");

    function chave(i, ordem) {
      if (ordem === "votos") { return -Number(i.dataset.votos); }
      if (ordem === "uf") { return i.dataset.uf + " " + norm(i.dataset.nome); }
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
        var ok = (!estado.tipo || i.dataset.tipo === estado.tipo) && (!estado.cargo || i.dataset.cargo === estado.cargo) && (!estado.grupo || (" " + i.dataset.grupo + " ").indexOf(" " + estado.grupo + " ") >= 0) &&
          (!termo || norm(i.dataset.nome).indexOf(termo) >= 0 || norm(i.dataset.partido).indexOf(termo) >= 0 ||
            (i.dataset.local && norm(i.dataset.local).indexOf(termo) >= 0));
        i.hidden = !ok;
        if (ok) { visiveis += 1; }
        alvo.appendChild(i);
      });
      contagem.textContent = visiveis === 0 ? "Ninguém encontrado. Tente outro nome ou volte para Todos."
        : "Mostrando " + visiveis + " de " + itens.length;
    }

    busca.addEventListener("input", aplicar);
    lista.querySelectorAll("button[data-grupo]").forEach(function (b) {
      b.addEventListener("click", function () {
        estado.grupo = b.dataset.grupo;
        b.parentNode.querySelectorAll("button").forEach(function (o) { o.setAttribute("aria-pressed", String(o === b)); });
        aplicar();
      });
    });
    [["tipo", "tipo"], ["cargo", "cargo"], ["grupo", "grupo"], ["ordem", "ordem"]].forEach(function (par) {
      var campo = lista.querySelector('[data-filtro="' + par[0] + '"]');
      if (campo) { campo.addEventListener("change", function () { estado[par[1]] = campo.value; aplicar(); }); }
    });
    aplicar();
  });

  // Busca de estado pelo nome ou pela sigla; sem JavaScript o campo fica escondido e a grade inteira aparece.
  var estados = document.getElementById("estados");
  var campoEstado = document.getElementById("busca-estado");
  if (estados && campoEstado) {
    campoEstado.parentNode.hidden = false;
    var avisoEstado = campoEstado.parentNode.querySelector(".contagem");
    campoEstado.addEventListener("input", function () {
      var termo = norm(campoEstado.value.trim());
      var visiveis = 0;
      estados.querySelectorAll(".estados").forEach(function (lista) {
        var algum = false;
        lista.querySelectorAll("li").forEach(function (li) {
          var ok = !termo || li.dataset.nome.indexOf(termo) >= 0;
          li.hidden = !ok;
          if (ok) { algum = true; visiveis += 1; }
        });
        lista.hidden = !algum;
        lista.previousElementSibling.hidden = !algum;
      });
      avisoEstado.textContent = visiveis === 0 ? "Nenhum estado encontrado. Tente outro nome ou a sigla." : "";
    });
  }

  // Compartilhar, como no theme.js do guia de identidade: abre o menu do aparelho (WhatsApp, redes, e-mail) com o
  // endereço canônico da página; sem ele, copia o link e troca o ícone por uma marca de verificação por 2 segundos.
  // Sem JavaScript o botão não aparece.
  var compartilhar = document.querySelector(".compartilhar");
  if (compartilhar && (navigator.share || (navigator.clipboard && navigator.clipboard.writeText))) {
    compartilhar.hidden = false;
    var iconeCompartilhar = compartilhar.innerHTML;
    var iconeFeito = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    var rotular = function (texto) { compartilhar.setAttribute("aria-label", texto); compartilhar.title = texto; };
    compartilhar.addEventListener("click", function () {
      var canonico = document.querySelector('link[rel="canonical"]');
      var url = canonico ? canonico.href : location.href.split("#")[0];
      if (navigator.share) {
        navigator.share({ title: document.title, url: url }).catch(function () { /* cancelado */ });
        return;
      }
      navigator.clipboard.writeText(url).then(function () {
        compartilhar.innerHTML = iconeFeito;
        rotular("Link copiado");
        setTimeout(function () {
          compartilhar.innerHTML = iconeCompartilhar;
          rotular("Compartilhar esta página");
        }, 2000);
      }).catch(function () { /* sem permissão para copiar */ });
    });
  }

  // Passar o mouse (ou focar) em um partido da legenda destaca as cadeiras dele no hemiciclo.
  document.querySelectorAll(".hemiciclo").forEach(function (h) {
    function destacar(g) {
      h.classList.toggle("destaque", g !== null);
      h.querySelectorAll("circle").forEach(function (c) { c.classList.toggle("ativo", g !== null && c.classList.contains("g" + g)); });
    }
    h.querySelectorAll("li[data-grupo]").forEach(function (li) {
      ["mouseenter", "focus"].forEach(function (ev) { li.addEventListener(ev, function () { destacar(li.dataset.grupo); }); });
      ["mouseleave", "blur"].forEach(function (ev) { li.addEventListener(ev, function () { destacar(null); }); });
    });
  });
})();
