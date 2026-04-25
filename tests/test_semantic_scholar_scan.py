import unittest

from scripts.semantic_scholar_scan import flatten_results, make_search_url, normalize_paper


class SemanticScholarScanTests(unittest.TestCase):
    def test_make_search_url_encodes_query_and_fields(self):
        url = make_search_url('"confined water" AFM', limit=7, fields="title,year")

        self.assertIn("query=%22confined+water%22+AFM", url)
        self.assertIn("limit=7", url)
        self.assertIn("fields=title%2Cyear", url)

    def test_normalize_paper_handles_missing_optional_fields(self):
        row = normalize_paper(
            "query",
            1,
            {
                "title": "Water bridge",
                "year": 2026,
                "citationCount": 3,
                "authors": [{"name": "A. Author"}],
                "externalIds": {"DOI": "10.0000/example"},
            },
        )

        self.assertEqual(row["title"], "Water bridge")
        self.assertEqual(row["doi"], "10.0000/example")
        self.assertEqual(row["authors"], "A. Author")
        self.assertEqual(row["venue"], "")
        self.assertEqual(row["abstract"], "")

    def test_flatten_results_keeps_query_context_and_rank(self):
        rows = flatten_results(
            [
                {
                    "query": "q1",
                    "response": {
                        "data": [
                            {"title": "A", "authors": []},
                            {"title": "B", "authors": []},
                        ]
                    },
                }
            ]
        )

        self.assertEqual([row["rank"] for row in rows], [1, 2])
        self.assertEqual([row["query"] for row in rows], ["q1", "q1"])
        self.assertEqual([row["title"] for row in rows], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
