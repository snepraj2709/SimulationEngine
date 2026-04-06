import { create } from "zustand";

interface UIState {
  selectedScenarioId: string | null;
  selectedICPId: string | null;
  compareScenarioIds: string[];
  setSelectedScenarioId: (scenarioId: string | null) => void;
  setSelectedICPId: (icpId: string | null) => void;
  toggleCompareScenario: (scenarioId: string) => void;
  clearCompareScenarios: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  selectedScenarioId: null,
  selectedICPId: null,
  compareScenarioIds: [],
  setSelectedScenarioId: (selectedScenarioId) => set({ selectedScenarioId }),
  setSelectedICPId: (selectedICPId) => set({ selectedICPId }),
  toggleCompareScenario: (scenarioId) => {
    const current = get().compareScenarioIds;
    if (current.includes(scenarioId)) {
      set({ compareScenarioIds: current.filter((item) => item !== scenarioId) });
      return;
    }
    set({ compareScenarioIds: [...current, scenarioId].slice(-3) });
  },
  clearCompareScenarios: () => set({ compareScenarioIds: [] }),
}));
