import { create } from "zustand";

interface UIState {
  selectedScenarioId: string | null;
  selectedICPId: string | null;
  compareICPIds: string[];
  compareScenarioIds: string[];
  setSelectedScenarioId: (scenarioId: string | null) => void;
  setSelectedICPId: (icpId: string | null) => void;
  toggleCompareICP: (icpId: string) => void;
  clearCompareICPs: () => void;
  toggleCompareScenario: (scenarioId: string) => void;
  clearCompareScenarios: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  selectedScenarioId: null,
  selectedICPId: null,
  compareICPIds: [],
  compareScenarioIds: [],
  setSelectedScenarioId: (selectedScenarioId) => set({ selectedScenarioId }),
  setSelectedICPId: (selectedICPId) => set({ selectedICPId }),
  toggleCompareICP: (icpId) => {
    const current = get().compareICPIds;
    if (current.includes(icpId)) {
      set({ compareICPIds: current.filter((item) => item !== icpId) });
      return;
    }
    set({ compareICPIds: [...current, icpId].slice(-3) });
  },
  clearCompareICPs: () => set({ compareICPIds: [] }),
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
