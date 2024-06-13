import unittest
from unittest import mock
import os
import strategoutil as sutil


class TestUtil(unittest.TestCase):
    POPEN_KWARGS = {"shell": True, "stdout": -1, "stderr": -1}

    def test_get_int_tuples_given_single_variable_simulate(self):
        verifyta_output = """
        -- Formula is satisfied.
        phase:
        [0]: (0,0) (4,0) (4,1) (17,1) (17,0) (25,0) (25,1) (36,1)
        """
        result = sutil.get_int_tuples(verifyta_output)
        expected = [(0,0), (4,0), (4,1), (17,1), (17,0), (25,0), (25,1), (36,1)]
        self.assertListEqual(result, expected)

    def test_get_float_tuples_given_single_variable_simulate(self):
        verifyta_output = """
        -- Formula is satisfied.
        x:
        [0]: (0,0.0) (4,0.0) (4,1.5) (17.456,1) (17.456,4.123456) (25.5,0.001) (25.5,1) (36,1)
        """
        result = sutil.get_float_tuples(verifyta_output)
        expected = [(0,0.0), (4,0.0), (4,1.5), (17.456,1), (17.456,4.123456), (25.5,0.001),
                    (25.5,1), (36,1)]
        self.assertListEqual(result, expected)

    def test_extract_state_given_single_variable_simulate(self):
        verifyta_output = """
-- Formula is satisfied.
x:
[0]: (0,0.0) (4,0.0) (4,1.5) (17.456,1) (17.456,4.123456) (25,0.000) (25,1) (36,1)
"""
        var = "x"
        controlperiod = 25
        result = sutil.extract_state(verifyta_output, var, controlperiod)
        expected = 1.0
        self.assertEqual(result, expected)

    def test_extract_state_given_single_variable_interpolate(self):
        verifyta_output = """
-- Formula is satisfied.
x:
[0]: (0,0.0) (4,0.0) (4,1.5) (17.456,1) (17.456,4.123456) (25,0.000) (25,1) (36,12.11)
"""
        var = "x"
        controlperiod = 35
        result = sutil.extract_state(verifyta_output, var, controlperiod)
        expected = 11.1
        self.assertEqual(result, expected)

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

    def test_array_to_stratego(self):
        str_array_in = str([0, 1, 2, 3, 4])
        str_array_out = sutil.array_to_stratego(str_array_in)
        self.assertEqual(str_array_out, "{0, 1, 2, 3, 4}")

    def test_merge_verifyta_args_given_empty(self):
        dict_input = {}
        result = sutil.merge_verifyta_args(dict_input)
        self.assertEqual(result, "")

    def test_merge_verifyta_args_given_arbitrary(self):
            dict_input = {
                "learning-method": "4",
                "good-runs": "100",
                "total-runs": "100",
                "runs-pr-state": "100",
                "eval-runs": "100",
                "max-iterations": "30",
                "filter": "0"
            }
            result = sutil.merge_verifyta_args(dict_input)
            expected = ("--learning-method 4 --good-runs 100 --total-runs 100 "
            "--runs-pr-state 100 --eval-runs 100 --max-iterations 30 --filter 0")
            self.assertEqual(result, expected)

    def test_run_stratego_model_only(self):
        with mock.patch("strategoutil.subprocess.Popen") as mock_Popen:
            sutil.run_stratego("model.xml", verifyta_command="$HOME/verifyta")
            # Below is the expected result with Popen default shell.
            expected = "$HOME/verifyta \"model.xml\""

            mock_Popen.assert_called_with(expected, **self.POPEN_KWARGS)

    def test_run_stratego_model_and_query(self):
        with mock.patch("strategoutil.subprocess.Popen") as mock_Popen:
            sutil.run_stratego("model.xml", "query.q")
            # Below is the expected result with Popen default shell.
            expected = "verifyta \"model.xml\" \"query.q\""
            mock_Popen.assert_called_with(expected, **self.POPEN_KWARGS)

    def test_run_stratego_all_variables(self):
        with mock.patch("strategoutil.subprocess.Popen") as mock_Popen:
            learning_args = {
                "learning-method": "4",
                "good-runs": "100",
                "total-runs": "100",
                "runs-pr-state": "100",
                "eval-runs": "100",
                "max-iterations": "30",
                "filter": "0"
            }
            sutil.run_stratego("model.xml", "query.q", learning_args, "verifyta")
            # Below is the expected result with Popen default shell.
            expected = ("verifyta \"model.xml\" \"query.q\" --learning-method 4 "
                        "--good-runs 100 --total-runs 100 --runs-pr-state 100 "
                        "--eval-runs 100 --max-iterations 30 --filter 0")
            mock_Popen.assert_called_with(expected, **self.POPEN_KWARGS)

    def test_successful_result_true(self):
        verifyta_output = """
        -- Formula is satisfied.
        x:
        [0]: (0,0.0) (4,0.0) (4,1.5) (17.456,1) (17.456,4.123456) (25,0.000) (25,1) (36,12.11)
        """
        result = sutil.successful_result(verifyta_output)
        self.assertTrue(result)

    def test_successful_result_false(self):
        verifyta_output = """
        -- Formula is not satisfied.
        x:
        [0]: (0,0.0) (4,0.0) (4,1.5) (17.456,1) (17.456,4.123456) (25,0.000) (25,1) (36,12.11)
        """
        result = sutil.successful_result(verifyta_output)
        self.assertFalse(result)

class TestFileInteraction(unittest.TestCase):
    def setUp(self):
        """
        Build dummy model files.
        """
        self.modelfile = "modelfile.xml"
        with open(self.modelfile, "w") as fin:
            fin.write(
            """
            some important definitions
            int important_variable_X = //TAG_X; 
            some more important definitions
            """)

    def tearDown(self):
        """
        Remove model file.
        """
        os.remove(self.modelfile)

    def test_insert_to_modelfile(self):
        tag = "//TAG_X"
        variable = "42"
        sutil.insert_to_modelfile(self.modelfile, tag, variable)

        with open(self.modelfile, "r") as fin:
            correct_substitution = "int important_variable_X = 42;" in fin.read()
            self.assertTrue(correct_substitution)
