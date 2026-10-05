/* Pure proposal assessment shared by the calculator and its tests. */
function avaliarProposta(valor, meta) {
  const invalida = {situacao: 'invalida'};
  if (!meta || valor === '' || valor == null) return invalida;
  const total = Number(valor);
  const material = Number(meta.md_anual) / 12;
  if (!Number.isFinite(total) || !Number.isFinite(material) || total < material || total < 0
      || !Number.isFinite(meta.ticket_alvo)) return invalida;
  const totalCentavos = Math.round(total * 100);
  const materialCentavos = Math.round(material * 100);
  const diferencaCentavos = totalCentavos - Math.round(meta.ticket_alvo * 100);
  return {situacao: diferencaCentavos >= 0 ? 'dentro' : 'abaixo', totalCentavos,
    materialCentavos, mensalidadeCentavos: totalCentavos - materialCentavos, diferencaCentavos};
}
