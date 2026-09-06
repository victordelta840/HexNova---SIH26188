from __future__ import annotations


class DeepLearningExplainability:
    @staticmethod
    def explain(global_similarity: float, region_analysis: list[dict[str, object]] | None = None, anomaly_score: float = 0.0) -> list[str]:
        explanations: list[str] = []
        if global_similarity >= 0.8:
            explanations.append("Global document features are highly consistent with the enrolled reference.")
        elif global_similarity >= 0.6:
            explanations.append("Global document structure is moderately consistent with the enrolled reference.")
        else:
            explanations.append("Visual pattern differs from the enrolled reference and requires review.")

        if region_analysis:
            worst_region = max(region_analysis, key=lambda item: (float(item.get("risk_score", 0)),))
            region_name = str(worst_region.get("region", "document region"))
            similarity = float(worst_region.get("similarity", 0.0))
            if similarity < 0.6:
                explanations.append(f"{region_name.replace('_', ' ')} shows a notable structural deviation from the reference.")
            elif similarity < 0.8:
                explanations.append(f"{region_name.replace('_', ' ')} shows a moderate deviation compared with the reference.")
        if anomaly_score >= 0.6:
            explanations.append("Suspicious structural deviation detected in the visual anomaly layer.")
        elif anomaly_score >= 0.35:
            explanations.append("A limited anomaly signal is present, but is not definitive on its own.")
        return explanations
