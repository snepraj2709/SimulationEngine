import { useQuery } from "@tanstack/react-query";

import { getAnalysis } from "@/api/analyses";

export function useAnalysisPolling(analysisId: string) {
  return useQuery({
    queryKey: ["analysis", analysisId],
    queryFn: () => getAnalysis(analysisId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "queued" || status === "processing") {
        return 3000;
      }
      return false;
    },
  });
}
