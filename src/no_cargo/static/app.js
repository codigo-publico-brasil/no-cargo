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
        var ok = (!estado.tipo || i.dataset.tipo === estado.tipo) && (!estado.cargo || i.dataset.cargo === estado.cargo) && (!estado.grupo || i.dataset.grupo === estado.grupo) &&
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
    var porTipo = lista.querySelector("#filtro-tipo");
    if (porTipo) { porTipo.addEventListener("change", function () { estado.tipo = porTipo.value; aplicar(); }); }
    var porCargo = lista.querySelector("#filtro-cargo");
    if (porCargo) { porCargo.addEventListener("change", function () { estado.cargo = porCargo.value; aplicar(); }); }
    var porOrdem = lista.querySelector("#filtro-ordem");
    if (porOrdem) { porOrdem.addEventListener("change", function () { estado.ordem = porOrdem.value; aplicar(); }); }
    aplicar();
  });

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
