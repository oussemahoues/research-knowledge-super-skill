import unittest

from src.evidence_research.ontology.compiler import compile_minimal_ontology, validate_ontology


class OntologyTests(unittest.TestCase):
    def test_competency_question_path(self):
        ontology = compile_minimal_ontology(
            {'target': 'supplier conformance'},
            {
                'entities': {'Supplier': {}, 'Product': {}, 'Specification': {}},
                'relations': {
                    'MANUFACTURES': {'domain': 'Supplier', 'range': 'Product'},
                    'VERIFIED_CONFORMANCE_TO': {'domain': 'Product', 'range': 'Specification'},
                },
                'competency_questions': [{'id': 'q1', 'start_type': 'Supplier', 'end_type': 'Specification'}],
            },
        )
        self.assertEqual(['MANUFACTURES', 'VERIFIED_CONFORMANCE_TO'], ontology['validated_paths']['q1'])

    def test_unanswerable_question_fails(self):
        result = validate_ontology({'entities': {'A': {}, 'B': {}}, 'relations': {}, 'competency_questions': [{'id': 'q1', 'start_type': 'A', 'end_type': 'B'}]})
        self.assertFalse(result.passed)


if __name__ == '__main__':
    unittest.main()
