from unittest import mock

from django.test import SimpleTestCase

from apps.graduate import services
from apps.graduate.models import Student


class PredictionListTests(SimpleTestCase):
    def test_batch_peer_trends_match_full_context(self):
        students = [
            Student(student_id=f"202301000{i}", name=f"Sample {i}",
                    grade="2023级", major="政治学理论", degree_type="master")
            for i in range(3)
        ]
        snapshots = [services.build_virtual_prediction_snapshot(s) for s in students]
        with (
            mock.patch.object(services, "build_prediction_sources", return_value=snapshots),
            mock.patch.object(services.PredictionIndicatorDefinition.objects, "all", return_value=[]),
            mock.patch.object(services, "module_notice_items", return_value=[]),
            mock.patch.object(services, "build_prediction_peer_references",
                              side_effect=AssertionError("List must not rebuild full peer contexts")),
        ):
            data = services.get_intelligent_prediction_data()
        self.assertEqual(len(data["students"]), 3)
        self.assertEqual(data["filters"]["default"]["grade"], "全部年级")
        for snapshot, row in zip(snapshots, data["students"]):
            reference = services.build_prediction_peer_references(snapshot, snapshots)
            expected = [v["value"] for v in reference["sameGrade"]["averageTrendIndex"]]
            self.assertEqual(row["peerTrend"], expected)
            self.assertEqual(row["peerAverageTrend"], expected)

    def test_peer_trends_exclude_self_and_handle_missing_months(self):
        rows = [
            {"grade": "2023级", "monthlyRecords": [{"month": "2026-01"}, {"month": "2026-02"}],
             "trendActual": [60, 70]},
            {"grade": "2023级", "monthlyRecords": [{"month": "2026-02"}], "trendActual": [90]},
            {"grade": "2024级", "monthlyRecords": [{"month": "2026-02"}], "trendActual": [50]},
        ]
        services.prediction_populate_list_peer_trends(rows)
        self.assertEqual(rows[0]["peerTrend"], [90])
        self.assertEqual(rows[1]["peerTrend"], [60, 70])
        self.assertEqual(rows[2]["peerTrend"], [])
