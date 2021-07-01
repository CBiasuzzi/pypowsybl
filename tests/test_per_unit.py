import unittest

import pypowsybl as pp
import pandas as pd
from numpy import NaN


class NetworkTestCase(unittest.TestCase):

    def test_bus_per_unit(self):
        n = pp.network.create_eurostag_tutorial_example1_network()
        pp.loadflow.run_ac(n)
        n.set_nominal_s(100)
        n.activate_per_unit()
        buses = n.get_buses()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['VLGEN_0', 'VLHV1_0', 'VLHV2_0', 'VLLOAD_0']),
                                columns=['v_mag', 'v_angle', 'connected_component', 'synchronous_component',
                                         'voltage_level_id'],
                                data=[[1.0208333333333333, 2.3259867733130872, 0, 0, 'VLGEN'],
                                      [1.0582705943555086, 0.0, 0, 0, 'VLHV1'],
                                      [1.026191191903048, -3.5063581039111074, 0, 0, 'VLHV2'],
                                      [0.9838574517801197, -9.614485847910167, 0, 0, 'VLLOAD']])
        pd.testing.assert_frame_equal(expected, buses, check_dtype=False)
        n.update_buses(pd.DataFrame(index=['VLGEN_0'], columns=['v_mag', 'v_angle'], data=[[1, 0]]))
        buses = n.get_buses()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['VLGEN_0', 'VLHV1_0', 'VLHV2_0', 'VLLOAD_0']),
                                columns=['v_mag', 'v_angle', 'connected_component', 'synchronous_component',
                                         'voltage_level_id'],
                                data=[[1, 0, 0, 0, 'VLGEN'],
                                      [1.05827, 0, 0, 0, 'VLHV1'],
                                      [1.02619, -3.50636, 0, 0, 'VLHV2'],
                                      [0.983857, -9.61449, 0, 0, 'VLLOAD']])
        pd.testing.assert_frame_equal(expected, buses, check_dtype=False)

    def test_generator_per_unit(self):
        n = pp.network.create_eurostag_tutorial_example1_network()
        pp.loadflow.run_ac(n)
        n.set_nominal_s(100)
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['GEN', 'GEN2']),
                                columns=['energy_source', 'target_p', 'min_p', 'max_p', 'min_q', 'max_q', 'target_v',
                                         'target_q', 'voltage_regulator_on', 'p',
                                         'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[['OTHER', 6.07, -99.9999, 99.9999, -99.9999, 99.9999, 1.02083, 3.01, True,
                                       -3.02781, -1.12641, 3.16461, 'VLGEN', 'VLGEN_0'],
                                      ['OTHER', 6.07, -99.9999, 99.9999, -1.79769e+306, 1.79769e+306, 1.02083, 3.01,
                                       True,
                                       -3.02781, -1.12641, 3.16461, 'VLGEN', 'VLGEN_0']])
        pd.testing.assert_frame_equal(expected, n.get_generators(), check_dtype=False)
        generators2 = pd.DataFrame(data=[[6.080, 3.020, 1.1, False]],
                                   columns=['target_p', 'target_q', 'target_v', 'voltage_regulator_on'], index=['GEN'])
        n.update_generators(generators2)
        expected = pd.DataFrame(index=pd.Series(name='id', data=['GEN', 'GEN2']),
                                columns=['energy_source', 'target_p', 'min_p', 'max_p', 'min_q', 'max_q', 'target_v',
                                         'target_q', 'voltage_regulator_on', 'p',
                                         'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[['OTHER', 6.08, -99.9999, 99.9999, -99.9999, 99.9999, 1.1, 3.02, False,
                                       -3.02781, -1.12641, 3.16461, 'VLGEN', 'VLGEN_0'],
                                      ['OTHER', 6.07, -99.9999, 99.9999, -1.79769e+306, 1.79769e+306,
                                       1.0208333333333333, 3.01,
                                       True,
                                       -3.02781, -1.12641, 3.16461, 'VLGEN', 'VLGEN_0']])
        pd.testing.assert_frame_equal(expected, n.get_generators(), check_dtype=False)

    def test_loads_per_unit(self):
        n = pp.network.create_eurostag_tutorial_example1_network()
        n.set_nominal_s(100)
        pp.loadflow.run_ac(n)
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['LOAD']),
                                columns=['type', 'p0', 'q0', 'p', 'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[['UNDEFINED', 6, 2, 6, 2, 6.42832, 'VLLOAD', 'VLLOAD_0']])
        pd.testing.assert_frame_equal(expected, n.get_loads(), check_dtype=False)
        n.update_loads(pd.DataFrame(data=[[5, 3]], columns=['p0', 'q0'], index=['LOAD']))
        expected = pd.DataFrame(index=pd.Series(name='id', data=['LOAD']),
                                columns=['type', 'p0', 'q0', 'p', 'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[['UNDEFINED', 5, 3, 6, 2, 6.42832, 'VLLOAD', 'VLLOAD_0']])
        pd.testing.assert_frame_equal(expected, n.get_loads(), check_dtype=False)

    def test_busbar_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        pp.loadflow.run_ac(n)
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id',
                                                data=['S1VL1_BBS', 'S1VL2_BBS1', 'S1VL2_BBS2', 'S2VL1_BBS', 'S3VL1_BBS',
                                                      'S4VL1_BBS']),
                                columns=['fictitious', 'v', 'angle', 'voltage_level_id'],
                                data=[[False, 0.998953, 2.40127, 'S1VL1'],
                                      [False, 1, 0, 'S1VL2'],
                                      [False, 1, 0, 'S1VL2'],
                                      [False, 1.02212, 0.734714, 'S2VL1'],
                                      [False, 1, 0, 'S3VL1'],
                                      [False, 1, -1.12594, 'S4VL1']])
        pd.testing.assert_frame_equal(expected, n.get_busbar_sections(), check_dtype=False)

    def test_hvdc_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        n.activate_per_unit()
        n.set_nominal_s(100)
        expected = pd.DataFrame(index=pd.Series(name='id', data=['HVDC1', 'HVDC2']),
                                columns=['converters_mode', 'active_power_setpoint', 'max_p', 'nominal_v', 'r',
                                         'converter_station1_id', 'converter_station2_id'],
                                data=[['SIDE_1_RECTIFIER_SIDE_2_INVERTER', 0.1, 3, 400, 0.000625, 'VSC1', 'VSC2'],
                                      ['SIDE_1_RECTIFIER_SIDE_2_INVERTER', 0.8, 3, 400, 0.000625, 'LCC1', 'LCC2']])
        pd.testing.assert_frame_equal(expected, n.get_hvdc_lines(), check_dtype=False)
        n.update_hvdc_lines(pd.DataFrame(data=[0.11], columns=['active_power_setpoint'], index=['HVDC1']))
        expected = pd.DataFrame(index=pd.Series(name='id', data=['HVDC1', 'HVDC2']),
                                columns=['converters_mode', 'active_power_setpoint', 'max_p', 'nominal_v', 'r',
                                         'converter_station1_id', 'converter_station2_id'],
                                data=[['SIDE_1_RECTIFIER_SIDE_2_INVERTER', 0.11, 3, 400, 0.000625, 'VSC1', 'VSC2'],
                                      ['SIDE_1_RECTIFIER_SIDE_2_INVERTER', 0.8, 3, 400, 0.000625, 'LCC1', 'LCC2']])
        pd.testing.assert_frame_equal(expected, n.get_hvdc_lines(), check_dtype=False)

    def test_lines_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        n.set_nominal_s(100)
        n.activate_per_unit()
        lines = n.get_lines()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['LINE_S2S3', 'LINE_S3S4']),
                                columns=['r', 'x', 'g1', 'b1', 'g2', 'b2', 'p1', 'q1', 'i1', 'p2', 'q2', 'i2',
                                         'voltage_level1_id', 'voltage_level2_id', 'bus1_id', 'bus2_id'],
                                data=[[0.00625, 11.9375, 0, 0, 0, 0, 1.09889, 1.90023, 2.14759, -1.09886, -1.84517,
                                       2.14759, 'S2VL1', 'S3VL1', 'S2VL1_0', 'S3VL1_0'],
                                      [0.00625, 8.1875, 0, 0, 0, 0, 2.40004, 0.021751, 2.40013, -2.4, 0.025415, 2.40013,
                                       'S3VL1', 'S4VL1', 'S3VL1_0', 'S4VL1_0']])
        pd.testing.assert_frame_equal(expected, lines, check_dtype=False)

    def test_two_windings_transformers_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        n.set_nominal_s(100)
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['TWT']),
                                columns=['r', 'x', 'g', 'b', 'rated_u1', 'rated_u2', 'rated_s', 'p1', 'q1', 'i1', 'p2',
                                         'q2', 'i2', 'voltage_level1_id', 'voltage_level2_id', 'bus1_id', 'bus2_id'],
                                data=[[1.25, 9.21562, 0, 5.12e-05, 1, 1, NaN, -0.8, -0.1, 0.807612, 0.800809,
                                       0.054857, 0.802686, 'S1VL1', 'S1VL2', 'S1VL1_0', 'S1VL2_0']])
        pd.testing.assert_frame_equal(expected, n.get_2_windings_transformers(), check_dtype=False)

    def test_three_windings_transformers_per_unit(self):
        # no network to test yet
        n = pp.network.create_four_substations_node_breaker_network()
        n.activate_per_unit()


    def test_shunt_compensators_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        n.activate_per_unit()
        n.set_nominal_s(100)
        expected = pd.DataFrame(index=pd.Series(name='id', data=['SHUNT']),
                                columns=['model_type', 'p', 'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[['LINEAR', NaN, 19.2, NaN, 'S1VL2', 'S1VL2_0']])
        pd.testing.assert_frame_equal(expected, n.get_shunt_compensators(), check_dtype=False)

    def test_dangling_lines_per_unit(self):
        n = pp.network._create_dangling_lines_network()
        pp.loadflow.run_ac(n)
        n.set_nominal_s(100)
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['DL']),
                                columns=['r', 'x', 'g', 'b', 'p0', 'q0', 'p', 'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[[100, 10, 0.001, 0.0001, 0.50, 0.30, 0.548154, 0.302926, 0.626289, 'VL', 'VL_0']])
        pd.testing.assert_frame_equal(expected, n.get_dangling_lines(), check_dtype=False)
        n.update_dangling_lines(pd.DataFrame(index=['DL'], columns=['p0', 'q0'], data=[[0.75, 0.25]]))
        expected = pd.DataFrame(index=pd.Series(name='id', data=['DL']),
                                columns=['r', 'x', 'g', 'b', 'p0', 'q0', 'p', 'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[[100, 10, 0.001, 0.0001, 0.75, 0.25, 0.548154, 0.302926, 0.626289, 'VL', 'VL_0']])
        pd.testing.assert_frame_equal(expected, n.get_dangling_lines(), check_dtype=False)

    def test_lcc_converter_stations_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        pp.loadflow.run_ac(n)
        n.set_nominal_s(100)
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['LCC1', 'LCC2']),
                                columns=['power_factor', 'loss_factor', 'p', 'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[[0.6, 1.1, 0.8088, 1.0784, 1.348, 'S1VL2', 'S1VL2_0'],
                                      [0.6, 1.1, -0.7912, 1.05493, 1.31867, 'S3VL1', 'S3VL1_0']])
        pd.testing.assert_frame_equal(expected, n.get_lcc_converter_stations(), check_dtype=False)

    def test_vsc_converter_stations_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        n.set_nominal_s(100)
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['VSC1', 'VSC2']),
                                columns=['voltage_setpoint', 'reactive_power_setpoint', 'voltage_regulator_on', 'p',
                                         'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[[1, 5, True, 0.1011, -5.12081, 5.12181, 'S1VL2', 'S1VL2_0'],
                                      [0, 1.2, False, -0.0989, -1.2, 1.17801, 'S2VL1', 'S2VL1_0']])
        pd.testing.assert_frame_equal(expected, n.get_vsc_converter_stations(), check_dtype=False)
        n.update_vsc_converter_stations(pd.DataFrame(data=[[3.0, 4.0], [1.0, 2.0]],
                                 columns=['voltage_setpoint', 'reactive_power_setpoint'], index=['VSC1', 'VSC2']))
        expected = pd.DataFrame(index=pd.Series(name='id', data=['VSC1', 'VSC2']),
                                columns=['voltage_setpoint', 'reactive_power_setpoint', 'voltage_regulator_on', 'p',
                                         'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[[3, 4, True, 0.1011, -5.12081, 5.12181, 'S1VL2', 'S1VL2_0'],
                                      [1, 2, False, -0.0989, -1.2, 1.17801, 'S2VL1', 'S2VL1_0']])
        pd.testing.assert_frame_equal(expected, n.get_vsc_converter_stations(), check_dtype=False)

    def test_get_static_var_compensators_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        pp.loadflow.run_ac(n)
        n.set_nominal_s(100)
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['SVC']),
                                columns=['voltage_setpoint', 'reactive_power_setpoint', 'regulation_mode', 'p',
                                         'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[[1.0, NaN, 'VOLTAGE', 0, -0.125415, 0.125415, 'S4VL1', 'S4VL1_0']])
        pd.testing.assert_frame_equal(expected, n.get_static_var_compensators(), check_dtype=False)

        n.update_static_var_compensators(pd.DataFrame(data=[[3.0, 4.0]],
                                 columns=['voltage_setpoint', 'reactive_power_setpoint'], index=['SVC']))
        expected = pd.DataFrame(index=pd.Series(name='id', data=['SVC']),
                                columns=['voltage_setpoint', 'reactive_power_setpoint', 'regulation_mode', 'p',
                                         'q', 'i', 'voltage_level_id', 'bus_id'],
                                data=[[3.0, 4.0, 'VOLTAGE', 0, -0.125415, 0.125415, 'S4VL1', 'S4VL1_0']])
        pd.testing.assert_frame_equal(expected, n.get_static_var_compensators(), check_dtype=False)

    def test_voltage_level_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        n.activate_per_unit()
        expected = pd.DataFrame(index=pd.Series(name='id', data=['S1VL1', 'S1VL2', 'S2VL1', 'S3VL1', 'S4VL1']),
                                columns=['substation_id', 'nominal_v', 'high_voltage_limit', 'low_voltage_limit'],
                                data=[['S1', 225, 1.06667, 0.977778], ['S1', 400, 1.1, 0.975], ['S2', 400, 1.1, 0.975],
                                      ['S3', 400, 1.1, 0.975], ['S4', 400, 1.1, 0.975]])
        pd.testing.assert_frame_equal(expected, n.get_voltage_levels(), check_dtype=False)

    def test_reactive_capability_curve_points_per_unit(self):
        n = pp.network.create_four_substations_node_breaker_network()
        n.set_nominal_s(100)
        n.activate_per_unit()
        expected = pd.DataFrame(
            index=pd.MultiIndex.from_tuples([('GH1', 0), ('GH1', 1), ('GH2', 0), ('GH2', 1), ('GH3', 0),
                                             ('GH3', 1), ('GTH1', 0), ('GTH1', 1), ('GTH2', 0), ('GTH2', 1),
                                             ('VSC1', 0), ('VSC1', 1)], names=['id', 'num']),
            columns=['p', 'min_q', 'max_q'],
            data=[[0, -7.693, 8.6], [1, -8.6455, 9.4625], [0, -5.568, 5.574], [2, -5.53514, 5.364],
                  [0, -6.806, 6.881], [2, -6.81725, 7.1635], [0, -0.768, 0.774],
                  [1, -0.73514, 0.764], [0, -1.693, 2], [4, -1.7455, 1.7625], [-1, -5.5, 5.7],
                  [1, -5.5, 5.7]])
        pd.testing.assert_frame_equal(expected, n.get_reactive_capability_curve_points(), check_dtype=False)


if __name__ == '__main__':
    unittest.main()
