const data = {
  PvP: {
    "4 Gate": {
      counter: "Defiende con 3 Gate Robo y usa Inmortales.",
      build: [
        "14 Pylon",
        "16 Gateway",
        "17 Assimilator",
        "19 Cybernetics Core",
        "21 Gateway x2",
        "24 Robotics Facility",
        "Saca Inmortales y mantén la pared"
      ]
    },
    "Cannon Rush": {
      counter: "Cancela el Nexus y destruye los cañones con Adeptos/Stalkers.",
      build: [
        "14 Pylon",
        "16 Gateway",
        "18 Assimilator",
        "20 Cybernetics Core",
        "20 Gateway",
        "Crono a Adeptos y destruye los cañones"
      ]
    }
  },
  PvZ: {
    "Zergling Rush": {
      counter: "Cierra la rampa con Zealots y usa escudos defensivos.",
      build: [
        "14 Pylon",
        "16 Gateway",
        "17 Assimilator",
        "20 Cybernetics Core",
        "22 Nexus",
        "Añade Forge para cañones defensivos"
      ]
    },
    "Roach Push": {
      counter: "Tres Gate Robo con Inmortales y Sentries para force fields.",
      build: [
        "14 Pylon",
        "16 Gateway",
        "17 Assimilator",
        "20 Cybernetics Core",
        "22 Nexus",
        "23 Gateway x2",
        "27 Robotics Facility",
        "Saca Inmortales y Sentries"
      ]
    }
  },
  PvT: {
    "Reaper Expand": {
      counter: "Defiende con Stalkers rápidos y contraataca con Blink.",
      build: [
        "14 Pylon",
        "16 Gateway",
        "17 Assimilator",
        "19 Cybernetics Core",
        "23 Nexus",
        "25 Twilight Council",
        "30 Blink + Gateways adicionales"
      ]
    },
    "1-1-1": {
      counter: "Temporiza con Blink Stalkers o Colosos rápidos.",
      build: [
        "14 Pylon",
        "16 Gateway",
        "17 Assimilator",
        "19 Cybernetics Core",
        "23 Nexus",
        "25 Robotics Facility",
        "30 Robotics Bay",
        "Saca Colosos y Gateways adicionales"
      ]
    }
  }
};

const matchupSelect = document.getElementById('matchup');
const strategySelect = document.getElementById('strategy');
const resultDiv = document.getElementById('result');

matchupSelect.addEventListener('change', () => {
  const matchup = matchupSelect.value;
  strategySelect.innerHTML = '';
  resultDiv.innerHTML = '';
  if (!matchup) {
    strategySelect.disabled = true;
    strategySelect.innerHTML = '<option value="">Seleccione un matchup primero</option>';
    return;
  }
  strategySelect.disabled = false;
  strategySelect.innerHTML = '<option value="">Seleccione</option>';
  Object.keys(data[matchup]).forEach(strat => {
    const opt = document.createElement('option');
    opt.value = strat;
    opt.textContent = strat;
    strategySelect.appendChild(opt);
  });
});

strategySelect.addEventListener('change', () => {
  const matchup = matchupSelect.value;
  const strat = strategySelect.value;
  if (!strat) {
    resultDiv.innerHTML = '';
    return;
  }
  const info = data[matchup][strat];
  const list = info.build.map(step => `<li>${step}</li>`).join('');
  resultDiv.innerHTML = `<h2>Counter: ${info.counter}</h2><ol>${list}</ol>`;
});
