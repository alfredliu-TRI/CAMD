#  Copyright (c) 2019 Toyota Research Institute.  All rights reserved.

import unittest
import os
import pandas as pd
import pickle
from monty.serialization import loadfn
from monty.tempfile import ScratchDir
from camd import CAMD_TEST_FILES
from camd.analysis import StabilityAnalyzer, AnalyzeStructures, GenericATFAnalyzer
from camd.utils.data import filter_dataframe_by_composition


class StabilityAnalyzerTest(unittest.TestCase):
    def test_plot_hull(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, "test_df_analysis.csv"),
                         index_col="id")
        df['Composition'] = df['formula']

        # Test 2D
        with ScratchDir('.'):
            analyzer = StabilityAnalyzer(hull_distance=0.1)
            filtered = filter_dataframe_by_composition(df, "TiO")
            analyzer.plot_hull(filtered, new_result_ids=["mp-685151", "mp-755875"],
                               filename="hull.png")
            self.assertTrue(os.path.isfile("hull.png"))

        # Test 3D
        with ScratchDir('.'):
            analyzer.hull_distance = 0.05
            filtered = filter_dataframe_by_composition(df, "TiNO")
            analyzer.plot_hull(filtered, new_result_ids=["mp-776280", "mp-30998"],
                               filename="hull.png")
            self.assertTrue(os.path.isfile("hull.png"))

    def test_analyze(self):
        df = pd.read_csv(os.path.join(CAMD_TEST_FILES, "test_df_analysis.csv"),
                         index_col="id")
        df['Composition'] = df['formula']
        analyzer = StabilityAnalyzer(hull_distance=0.1)
        seed_data = filter_dataframe_by_composition(df, "TiNO")
        # TODO: resolve drop_duplicates filtering mp data
        seed_data = seed_data.drop_duplicates(keep='last').dropna()
        new_exp_indices = ["mp-30998", "mp-572822"]
        new_experimental_results = seed_data.loc[new_exp_indices]
        seed_data = seed_data.drop(index=new_exp_indices)
        summary, seed_data = analyzer.analyze(
            new_experimental_results=seed_data, seed_data=pd.DataFrame(),
        )
        summary, new_seed = analyzer.analyze(
            new_experimental_results=new_experimental_results,
            seed_data=seed_data
        )
        self.assertAlmostEqual(new_seed.loc['mp-30998', 'stability'], 0)
        self.assertAlmostEqual(new_seed.loc["mp-572822", 'stability'], 0.52784795)
        self.assertTrue(new_seed.loc['mp-30998', 'is_stable'])
        self.assertFalse(new_seed.loc["mp-572822", 'is_stable'])


class StructureAnalyzerTest(unittest.TestCase):
    def test_analyze_vaspqmpy_jobs(self):
        jobs = pd.read_pickle(os.path.join(CAMD_TEST_FILES, "mn-ni-o-sb.pickle"))
        analyzer = AnalyzeStructures()
        self.assertEqual(analyzer.analyze_vaspqmpy_jobs(jobs, against_icsd=True, use_energies=False),
                         [True, True, True])

        self.assertEqual(analyzer.analyze_vaspqmpy_jobs(jobs, against_icsd=True, use_energies=True),
                         [True, True, True])


class GenericATFAnalyzerTest(unittest.TestCase):
    def test_analyze(self):
        seed_size = 10
        exploration_df = pd.read_csv(os.path.join(CAMD_TEST_FILES, "test_df_ATF.csv"))
        record = pickle.load(open(os.path.join(CAMD_TEST_FILES, "seed_data_ATF.pickle"), "rb"))
        analyzer = GenericATFAnalyzer(exploration_df, percentile=0.01)
        seed_data = pd.DataFrame(record[:seed_size])
        new_experimental_results = pd.DataFrame(record[seed_size:])
        summary, _ = analyzer.analyze(new_experimental_results, seed_data)

        self.assertEqual(summary['deALM'].to_list()[0].shape[0], record.shape[0]-seed_size)
        self.assertEqual(summary['anyALM'].to_list()[0].shape[0], record.shape[0]-seed_size)
        self.assertEqual(summary['allALM'].to_list()[0].shape[0], record.shape[0]-seed_size)
        self.assertEqual(summary['simALM'].to_list()[0].shape[0], record.shape[0]-seed_size)


if __name__ == '__main__':
    unittest.main()
