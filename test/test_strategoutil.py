import unittest
import strategoutil as sutil

class TestStrategoUtils(unittest.TestCase):

    def test_get_int_tuples_give_single_variable_simulate(self):
        verifyta_output =  """
        -- Formula is satisfied.
        phase:
        [0]: (0,0) (4,0) (4,1) (17,1) (17,0) (25,0) (25,1) (36,1)
        """
        result = sutil.get_int_tuples(verifyta_output)
        expected = [(0,0), (4,0), (4,1), (17,1), (17,0), (25,0), (25,1), (36,1)]
        self.assertListEqual(result, expected)

    def test_get_duration_action_given_empty_input(self):
        input_case = []
        result = sutil.get_duration_action(input_case)
        expected = []
        self.assertListEqual(result, expected)

    def test_get_duration_action_given_arbitrary_input(self):
        input_case = [(0,0), (4,0), (4,1), (17,1), (17,0), (25,0), (25,1), (36,1)]
        result = sutil.get_duration_action(input_case)
        expected = [(4, 0), (13, 1), (8, 0), (11, 1)]
        self.assertListEqual(result, expected)


