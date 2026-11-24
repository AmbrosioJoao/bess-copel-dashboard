const faultButton = document.getElementById("faultButton");
const occurrencePanel = document.getElementById("occurrencePanel");
const resolveButton = document.getElementById("resolveButton");
const diagramStage = document.getElementById("diagramStage");

const statusTag = document.getElementById("statusTag");
const batteryVoltage = document.getElementById("batteryVoltage");
const voltageHint = document.getElementById("voltageHint");
const savingsValue = document.getElementById("savingsValue");
const savingsHint = document.getElementById("savingsHint");
const faultVoltage = document.getElementById("faultVoltage");
const occurrenceState = document.getElementById("occurrenceState");
const occurrenceText = document.getElementById("occurrenceText");
const detailLocation = document.getElementById("detailLocation");
const detailCause = document.getElementById("detailCause");
const detailAction = document.getElementById("detailAction");

const states = {
  active: {
    voltage: "792",
    voltageHint: "CC · banco em descarga",
    savings: "R$ 18.450",
    savingsHint: "por mês · evita reforço de rede",
    faultVoltage: "0,93 pu",
    tag: "Ocorrência ativa",
    tagClass: "tag alarm",
    state: "Aberta",
    text: "Queda de tensão entre T1 e o religador R1. O pico de irrigação e a distância do trecho derrubam a tensão antes da carga B.",
    location: "Trecho 2 · entre T1 e R1",
    cause: "Pico de irrigação",
    action: "BESS injeta potência e sustenta a tensão",
    button: "Aplicar BESS e encerrar",
    marker: "!",
    aria: "Falha ativa: queda de tensão entre T1 e R1"
  },
  resolved: {
    voltage: "812",
    voltageHint: "CC · tensão estabilizada",
    savings: "R$ 20.300",
    savingsHint: "por mês · reforço de rede evitado",
    faultVoltage: "1,00 pu",
    tag: "Alimentador estável",
    tagClass: "tag ok",
    state: "Encerrada",
    text: "O BESS assumiu a descarga no ponto de conexão e recuperou a tensão do trecho, evitando o reforço da rede.",
    location: "Trecho 2 · entre T1 e R1",
    cause: "Corrigida pelo BESS",
    action: "Monitoramento mantido pelo operador",
    button: "Reabrir ocorrência (demonstração)",
    marker: "✓",
    aria: "Falha encerrada: alimentador estável"
  }
};

let resolved = false;

function render() {
  const state = resolved ? states.resolved : states.active;

  batteryVoltage.textContent = state.voltage;
  voltageHint.textContent = state.voltageHint;
  savingsValue.textContent = state.savings;
  savingsHint.textContent = state.savingsHint;
  faultVoltage.textContent = state.faultVoltage;
  statusTag.textContent = state.tag;
  statusTag.className = state.tagClass;
  occurrenceState.textContent = state.state;
  occurrenceText.textContent = state.text;
  detailLocation.textContent = state.location;
  detailCause.textContent = state.cause;
  detailAction.textContent = state.action;
  resolveButton.textContent = state.button;
  faultButton.textContent = state.marker;
  faultButton.setAttribute("aria-label", state.aria);
  faultButton.classList.toggle("resolved", resolved);
  diagramStage.classList.toggle("resolved", resolved);
}

faultButton.addEventListener("click", () => {
  const isOpen = !occurrencePanel.hidden;
  occurrencePanel.hidden = isOpen;
  faultButton.setAttribute("aria-expanded", String(!isOpen));

  if (!isOpen) {
    occurrencePanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
});

resolveButton.addEventListener("click", () => {
  resolved = !resolved;
  render();
});

render();
