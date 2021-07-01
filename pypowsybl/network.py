#
# Copyright (c) 2020, RTE (http://www.rte-france.com)
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import math

import _pypowsybl
import sys
from _pypowsybl import ElementType
from _pypowsybl import PyPowsyblError
from typing import List
from typing import Set

import pandas as pd
import datetime


from pypowsybl.util import create_data_frame_from_series_array


class SingleLineDiagram:
    """ This class represents a single line diagram."""

    def __init__(self, svg: str):
        self._svg = svg

    @property
    def svg(self):
        return self._svg

    def __str__(self):
        return self._svg

    def _repr_svg_(self):
        return self._svg


class Network(object):
    def __init__(self, handle):
        self._handle = handle
        att = _pypowsybl.get_network_metadata(self._handle)
        self._id = att.id
        self._name = att.name
        self._source_format = att.source_format
        self._forecast_distance = datetime.timedelta(minutes=att.forecast_distance)
        self._case_date = datetime.datetime.utcfromtimestamp(att.case_date)
        self.nominal_s = 1  # MWatt
        self.per_unit = False
        self.sqrt3 = math.sqrt(3)

    @property
    def id(self) -> str:
        """
        ID of this network
        """
        return self._id

    @property
    def name(self) -> str:
        """
        Name of this network
        """
        return self._name

    @property
    def source_format(self) -> str:
        """
        Format of the source where this network came from.
        """
        return self._source_format

    @property
    def case_date(self) -> datetime.datetime:
        """
        Date of this network case, in UTC timezone.
        """
        return self._case_date

    @property
    def forecast_distance(self) -> datetime.timedelta:
        """
        The forecast distance: 0 for a snapshot.
        """
        return self._forecast_distance

    def __str__(self) -> str:
        return f'Network(id={self.id}, name={self.name}, case_date={self.case_date}, ' \
               f'forecast_distance={self.forecast_distance}, source_format={self.source_format})'

    def __repr__(self) -> str:
        return str(self)

    def __getstate__(self):
        return {'xml': self.dump_to_string()}

    def __setstate__(self, state):
        xml = state['xml']
        n = _pypowsybl.load_network_from_string('tmp.xiidm', xml, {})
        self._handle = n

    def activate_per_unit(self):
        self.per_unit = True

    def desactivate_per_unit(self):
        self.per_unit = False

    def set_nominal_s(self, nominal_s):
        self.nominal_s = nominal_s

    def open_switch(self, id: str):
        return _pypowsybl.update_switch_position(self._handle, id, True)

    def close_switch(self, id: str):
        return _pypowsybl.update_switch_position(self._handle, id, False)

    def connect(self, id: str):
        return _pypowsybl.update_connectable_status(self._handle, id, True)

    def disconnect(self, id: str):
        return _pypowsybl.update_connectable_status(self._handle, id, False)

    def dump(self, file: str, format: str = 'XIIDM', parameters: dict = {}):
        """Save a network to a file using a specified format.

        Args:
            file (str): a file
            format (str, optional): format to save the network, defaults to 'XIIDM'
            parameters (dict, optional): a map of parameters
        """
        _pypowsybl.dump_network(self._handle, file, format, parameters)

    def dump_to_string(self, format: str = 'XIIDM', parameters: dict = {}) -> str:
        """Save a network to a string using a specified format.

        Args:
            format (str, optional): format to export, only support mono file type, defaults to 'XIIDM'
            parameters (dict, optional): a map of parameters

        Returns:
            a string representing network
        """
        return _pypowsybl.dump_network_to_string(self._handle, format, parameters)

    def reduce(self, v_min: float = 0, v_max: float = sys.float_info.max, ids: List[str] = [],
               vl_depths: tuple = (), with_dangling_lines: bool = False):
        vls = []
        depths = []
        for v in vl_depths:
            vls.append(v[0])
            depths.append(v[1])
        _pypowsybl.reduce_network(self._handle, v_min, v_max, ids, vls, depths, with_dangling_lines)

    def write_single_line_diagram_svg(self, container_id: str, svg_file: str):
        """ Create a single line diagram in SVG format from a voltage level or a substation and write to a file.

        Args:
            container_id: a voltage level id or a substation id
            svg_file: a svg file path
        """
        _pypowsybl.write_single_line_diagram_svg(self._handle, container_id, svg_file)

    def get_single_line_diagram(self, container_id: str):
        """ Create a single line diagram from a voltage level or a substation.

        Args:
            container_id: a voltage level id or a substation id

        Returns:
            the single line diagram
        """
        return SingleLineDiagram(_pypowsybl.get_single_line_diagram_svg(self._handle, container_id))

    def get_elements_ids(self, element_type: _pypowsybl.ElementType, nominal_voltages: Set[float] = None,
                         countries: Set[str] = None,
                         main_connected_component: bool = True, main_synchronous_component: bool = True,
                         not_connected_to_same_bus_at_both_sides: bool = False) -> List[str]:
        return _pypowsybl.get_network_elements_ids(self._handle, element_type,
                                                   [] if nominal_voltages is None else list(nominal_voltages),
                                                   [] if countries is None else list(countries),
                                                   main_connected_component, main_synchronous_component,
                                                   not_connected_to_same_bus_at_both_sides)

    def get_elements(self, element_type: _pypowsybl.ElementType) -> pd.DataFrame:
        """ Get network elements as a ``Pandas`` data frame for a specified element type.

        Args:
            element_type (ElementType): the element type
        Returns:
            a network elements data frame for the specified element type
        """
        series_array = _pypowsybl.create_network_elements_series_array(self._handle, element_type)
        return create_data_frame_from_series_array(series_array)

    def get_buses(self) -> pd.DataFrame:
        if self.per_unit:
            join = pd.merge(self.get_elements(_pypowsybl.ElementType.BUS), self.get_voltage_levels()['nominal_v'],
                            left_on='voltage_level_id', right_index=True)
            join['v_mag'] = join['v_mag'] / join['nominal_v']
            return join.drop('nominal_v', axis=1)
        else:
            return self.get_elements(_pypowsybl.ElementType.BUS)

    def get_generators(self) -> pd.DataFrame:
        """ Get generators as a ``Pandas`` data frame.

        Returns:
            a generators data frame
        """
        generators = self.get_elements(_pypowsybl.ElementType.GENERATOR)
        if self.per_unit:
            generators['target_p'] /= self.nominal_s
            generators['target_q'] /= self.nominal_s
            generators['min_p'] /= self.nominal_s
            generators['min_q'] /= self.nominal_s
            generators['max_p'] /= self.nominal_s
            generators['max_q'] /= self.nominal_s
            generators['p'] /= self.nominal_s
            generators['q'] /= self.nominal_s
            join = pd.merge(generators, self.get_voltage_levels()['nominal_v'],
                            left_on='voltage_level_id', right_index=True)
            join['target_v'] = join['target_v'] / join['nominal_v']
            join['i'] /= self.nominal_s * 10 ** 3 / (self.sqrt3 * join['nominal_v'])
            generators = join.drop('nominal_v', axis=1)
        return generators

    def get_loads(self) -> pd.DataFrame:
        """ Get loads as a ``Pandas`` data frame.

        Returns:
            a loads data frame
        """
        loads = self.get_elements(_pypowsybl.ElementType.LOAD)
        if self.per_unit:
            loads['p0'] /= self.nominal_s
            loads['q0'] /= self.nominal_s
            loads['p'] /= self.nominal_s
            loads['q'] /= self.nominal_s
            join = pd.merge(loads, self.get_voltage_levels()['nominal_v'],
                            left_on='voltage_level_id', right_index=True)
            join['i'] /= self.nominal_s * 10 ** 3 / (self.sqrt3 * join['nominal_v'])
            loads = join.drop('nominal_v', axis=1)
        return loads

    def get_batteries(self) -> pd.DataFrame:
        """ Get batteries as a ``Pandas`` data frame.

        Returns:
            a batteries data frame
        """
        return self.get_elements(_pypowsybl.ElementType.BATTERY)

    def get_lines(self) -> pd.DataFrame:
        """ Get lines as a ``Pandas`` data frame.

        Returns:
            a lines data frame
        """
        lines = self.get_elements(_pypowsybl.ElementType.LINE)
        if self.per_unit:
            lines['p1'] /= self.nominal_s
            lines['p2'] /= self.nominal_s
            lines['q1'] /= self.nominal_s
            lines['q2'] /= self.nominal_s
            lines = pd.merge(lines, self.get_voltage_levels()['nominal_v'],
                             left_on='voltage_level1_id', right_index=True)
            lines['i1'] /= self.nominal_s * 10 ** 3 / (self.sqrt3 * lines['nominal_v'])
            lines['i2'] /= self.nominal_s * 10 ** 3 / (self.sqrt3 * lines['nominal_v'])
            lines['r'] /= lines['nominal_v'] ** 2 / (self.nominal_s * 10 ** 3)
            lines['x'] /= lines['nominal_v'] ** 2 / (self.nominal_s * 10 ** 3)
            lines['g1'] /= (self.nominal_s * 10 ** 3) / lines['nominal_v'] ** 2
            lines['g2'] /= (self.nominal_s * 10 ** 3) / lines['nominal_v'] ** 2
            lines['b1'] /= (self.nominal_s * 10 ** 3) / lines['nominal_v'] ** 2
            lines['b2'] /= (self.nominal_s * 10 ** 3) / lines['nominal_v'] ** 2
            lines = lines.drop('nominal_v', axis=1)
        return lines

    def get_2_windings_transformers(self) -> pd.DataFrame:
        """ Get 2 windings transformers as a ``Pandas`` data frame.

        Returns:
            a 2 windings transformers data frame
        """
        two_windings_transformers = self.get_elements(_pypowsybl.ElementType.TWO_WINDINGS_TRANSFORMER)
        if self.per_unit:
            two_windings_transformers['p1'] /= self.nominal_s
            two_windings_transformers['q1'] /= self.nominal_s
            two_windings_transformers['p2'] /= self.nominal_s
            two_windings_transformers['q2'] /= self.nominal_s
            two_windings_transformers = pd.merge(two_windings_transformers, self.get_voltage_levels()['nominal_v'],
                                                 left_on='voltage_level1_id', right_index=True)
            two_windings_transformers.rename(columns={'nominal_v': 'nominal_v1'}, inplace=True)
            two_windings_transformers = pd.merge(two_windings_transformers, self.get_voltage_levels()['nominal_v'],
                                                 left_on='voltage_level2_id', right_index=True)
            two_windings_transformers.rename(columns={'nominal_v': 'nominal_v2'}, inplace=True)
            two_windings_transformers['i1'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * two_windings_transformers['nominal_v1'])
            two_windings_transformers['i2'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * two_windings_transformers['nominal_v2'])
            two_windings_transformers['r'] /= two_windings_transformers['nominal_v2'] ** 2 / (self.nominal_s * 10 ** 3)
            two_windings_transformers['x'] /= two_windings_transformers['nominal_v2'] ** 2 / (self.nominal_s * 10 ** 3)
            two_windings_transformers['g'] /= (self.nominal_s * 10 ** 3) / two_windings_transformers['nominal_v2'] ** 2
            two_windings_transformers['b'] /= (self.nominal_s * 10 ** 3) / two_windings_transformers['nominal_v2'] ** 2
            two_windings_transformers['rated_u1'] /= two_windings_transformers['nominal_v1']
            two_windings_transformers['rated_u2'] /= two_windings_transformers['nominal_v2']
            two_windings_transformers = two_windings_transformers.drop(['nominal_v1', 'nominal_v2'], axis=1)
        return two_windings_transformers

    def get_3_windings_transformers(self) -> pd.DataFrame:
        """ Get 3 windings transformers as a ``Pandas`` data frame.

        Returns:
            a 3 windings transformers data frame
        """
        three_windings_transformers = self.get_elements(_pypowsybl.ElementType.THREE_WINDINGS_TRANSFORMER)
        if self.per_unit:
            three_windings_transformers['p1'] /= self.nominal_s
            three_windings_transformers['q1'] /= self.nominal_s
            three_windings_transformers['p2'] /= self.nominal_s
            three_windings_transformers['q2'] /= self.nominal_s
            three_windings_transformers['p3'] /= self.nominal_s
            three_windings_transformers['q3'] /= self.nominal_s
            three_windings_transformers = pd.merge(three_windings_transformers, self.get_voltage_levels()['nominal_v'],
                                                 left_on='voltage_level1_id', right_index=True)
            three_windings_transformers.rename(columns={'nominal_v': 'nominal_v1'}, inplace=True)
            three_windings_transformers = pd.merge(three_windings_transformers, self.get_voltage_levels()['nominal_v'],
                                                 left_on='voltage_level2_id', right_index=True)
            three_windings_transformers.rename(columns={'nominal_v': 'nominal_v2'}, inplace=True)
            three_windings_transformers = pd.merge(three_windings_transformers, self.get_voltage_levels()['nominal_v'],
                                                   left_on='voltage_level3_id', right_index=True)
            three_windings_transformers.rename(columns={'nominal_v': 'nominal_v3'}, inplace=True)
            three_windings_transformers['i1'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * three_windings_transformers['nominal_v1'])
            three_windings_transformers['i2'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * three_windings_transformers['nominal_v2'])
            three_windings_transformers['i3'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * three_windings_transformers['nominal_v3'])
            three_windings_transformers['r1'] /= three_windings_transformers['nominal_v1'] ** 2 / (self.nominal_s * 10 ** 3)
            three_windings_transformers['x1'] /= three_windings_transformers['nominal_v1'] ** 2 / (self.nominal_s * 10 ** 3)
            three_windings_transformers['g1'] /= (self.nominal_s * 10 ** 3) / three_windings_transformers['nominal_v1'] ** 2
            three_windings_transformers['b1'] /= (self.nominal_s * 10 ** 3) / three_windings_transformers['nominal_v1'] ** 2
            three_windings_transformers['r2'] /= three_windings_transformers['nominal_v2'] ** 2 / (
                        self.nominal_s * 10 ** 3)
            three_windings_transformers['x2'] /= three_windings_transformers['nominal_v2'] ** 2 / (
                        self.nominal_s * 10 ** 3)
            three_windings_transformers['g2'] /= (self.nominal_s * 10 ** 3) / three_windings_transformers[
                'nominal_v2'] ** 2
            three_windings_transformers['b2'] /= (self.nominal_s * 10 ** 3) / three_windings_transformers[
                'nominal_v2'] ** 2
            three_windings_transformers['r3'] /= three_windings_transformers['nominal_v3'] ** 2 / (
                        self.nominal_s * 10 ** 3)
            three_windings_transformers['x3'] /= three_windings_transformers['nominal_v3'] ** 2 / (
                        self.nominal_s * 10 ** 3)
            three_windings_transformers['g3'] /= (self.nominal_s * 10 ** 3) / three_windings_transformers[
                'nominal_v3'] ** 2
            three_windings_transformers['b3'] /= (self.nominal_s * 10 ** 3) / three_windings_transformers[
                'nominal_v3'] ** 2
            three_windings_transformers['rated_u1'] /= three_windings_transformers['nominal_v1']
            three_windings_transformers['rated_u2'] /= three_windings_transformers['nominal_v2']
            three_windings_transformers['rated_u3'] /= three_windings_transformers['nominal_v3']
            three_windings_transformers = three_windings_transformers.drop(['nominal_v1', 'nominal_v2', 'nominal_v3'], axis=1)
        return three_windings_transformers

    def get_shunt_compensators(self) -> pd.DataFrame:
        """ Get shunt compensators as a ``Pandas`` data frame.

        Returns:
            a shunt compensators data frame
        """
        shunt_compensators = self.get_elements(_pypowsybl.ElementType.SHUNT_COMPENSATOR)
        if self.per_unit:
            shunt_compensators['p'] /= self.nominal_s
            shunt_compensators['q'] /= self.nominal_s
        return shunt_compensators

    def get_dangling_lines(self) -> pd.DataFrame:
        """ Get dangling lines as a ``Pandas`` data frame.

        Returns:
            a dangling lines data frame
        """
        dangling_lines = self.get_elements(_pypowsybl.ElementType.DANGLING_LINE)
        if self.per_unit:
            dangling_lines['p'] /= self.nominal_s
            dangling_lines['q'] /= self.nominal_s
            dangling_lines['p0'] /= self.nominal_s
            dangling_lines['q0'] /= self.nominal_s
            dangling_lines = pd.merge(dangling_lines, self.get_voltage_levels()['nominal_v'],
                                      left_on='voltage_level_id', right_index=True)
            dangling_lines['i'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * dangling_lines['nominal_v'])
            dangling_lines['r'] /= dangling_lines['nominal_v'] ** 2 / (self.nominal_s * 10 ** 3)
            dangling_lines['x'] /= dangling_lines['nominal_v'] ** 2 / (self.nominal_s * 10 ** 3)
            dangling_lines['g'] /= dangling_lines['nominal_v'] ** 2 / (self.nominal_s * 10 ** 3)
            dangling_lines['b'] /= dangling_lines['nominal_v'] ** 2 / (self.nominal_s * 10 ** 3)
            dangling_lines = dangling_lines.drop('nominal_v', axis=1)
        return dangling_lines

    def get_lcc_converter_stations(self) -> pd.DataFrame:
        """ Get LCC converter stations as a ``Pandas`` data frame.

        Returns:
            a LCC converter stations data frame
        """
        lcc_converter_stations = self.get_elements(_pypowsybl.ElementType.LCC_CONVERTER_STATION)
        if self.per_unit:
            lcc_converter_stations['p'] /= self.nominal_s
            lcc_converter_stations['q'] /= self.nominal_s
            lcc_converter_stations = pd.merge(lcc_converter_stations, self.get_voltage_levels()['nominal_v'],
                                              left_on='voltage_level_id', right_index=True)
            lcc_converter_stations['i'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * lcc_converter_stations['nominal_v'])
            lcc_converter_stations = lcc_converter_stations.drop('nominal_v', axis=1)
        return lcc_converter_stations

    def get_vsc_converter_stations(self) -> pd.DataFrame:
        """ Get VSC converter stations as a ``Pandas`` data frame.

        Returns:
            a VSC converter stations data frame
        """
        vsc_converter_stations = self.get_elements(_pypowsybl.ElementType.VSC_CONVERTER_STATION)
        if self.per_unit:
            vsc_converter_stations['p'] /= self.nominal_s
            vsc_converter_stations['q'] /= self.nominal_s
            vsc_converter_stations['reactive_power_setpoint'] /= self.nominal_s
            vsc_converter_stations = pd.merge(vsc_converter_stations, self.get_voltage_levels()['nominal_v'],
                                              left_on='voltage_level_id', right_index=True)
            vsc_converter_stations['i'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * vsc_converter_stations['nominal_v'])
            vsc_converter_stations['voltage_setpoint'] /=  vsc_converter_stations['nominal_v']
            vsc_converter_stations = vsc_converter_stations.drop('nominal_v', axis=1)
        return vsc_converter_stations

    def get_static_var_compensators(self) -> pd.DataFrame:
        """ Get static var compensators as a ``Pandas`` data frame.

        Returns:
            a static var compensators data frame
        """
        static_var_compensators = self.get_elements(_pypowsybl.ElementType.STATIC_VAR_COMPENSATOR)
        if self.per_unit:
            static_var_compensators['p'] /= self.nominal_s
            static_var_compensators['q'] /= self.nominal_s
            static_var_compensators['reactive_power_setpoint'] /= self.nominal_s
            static_var_compensators = pd.merge(static_var_compensators, self.get_voltage_levels()['nominal_v'],
                                               left_on='voltage_level_id', right_index=True)
            static_var_compensators['i'] /= self.nominal_s * 10 ** 3 / (
                    self.sqrt3 * static_var_compensators['nominal_v'])
            static_var_compensators['voltage_setpoint'] /= static_var_compensators['nominal_v']
            static_var_compensators = static_var_compensators.drop('nominal_v', axis=1)
        return static_var_compensators

    def get_voltage_levels(self) -> pd.DataFrame:
        """ Get voltage levels as a ``Pandas`` data frame.

        Returns:
            a voltage levels data frame
        """
        voltage_levels = self.get_elements(_pypowsybl.ElementType.VOLTAGE_LEVEL)
        if self.per_unit:
            voltage_levels['high_voltage_limit'] /= voltage_levels['nominal_v']
            voltage_levels['low_voltage_limit'] /= voltage_levels['nominal_v']
        return voltage_levels

    def get_busbar_sections(self) -> pd.DataFrame:
        """ Get busbar sections as a ``Pandas`` data frame.

        Returns:
            a busbar sections data frame
        """
        busbar_sections = self.get_elements(_pypowsybl.ElementType.BUSBAR_SECTION)
        if self.per_unit:
            join = pd.merge(busbar_sections, self.get_voltage_levels()['nominal_v'],
                            left_on='voltage_level_id', right_index=True)
            join['v'] /= join['nominal_v']
            busbar_sections = join.drop('nominal_v', axis=1)
        return busbar_sections

    def get_substations(self) -> pd.DataFrame:
        """ Get substations ``Pandas`` data frame.

        Returns:
            a substations data frame
        """
        return self.get_elements(_pypowsybl.ElementType.SUBSTATION)

    def get_hvdc_lines(self) -> pd.DataFrame:
        """ Get HVDC lines as a ``Pandas`` data frame.

        Returns:
            a HVDC lines data frame
        """
        hvdc_lines = self.get_elements(_pypowsybl.ElementType.HVDC_LINE)
        if self.per_unit:
            hvdc_lines['max_p'] /= self.nominal_s
            hvdc_lines['active_power_setpoint'] /= self.nominal_s
            hvdc_lines['r'] /= hvdc_lines['nominal_v'] ** 2 / self.nominal_s
        return hvdc_lines

    def get_switches(self) -> pd.DataFrame:
        """ Get switches as a ``Pandas`` data frame.

        Returns:
            a switches data frame
        """
        return self.get_elements(_pypowsybl.ElementType.SWITCH)

    def get_ratio_tap_changer_steps(self) -> pd.DataFrame:
        """ Get ratio tap changer steps as a ``Pandas`` data frame.

        Returns:
            a ratio tap changer steps data frame
        """
        ratio_tap_changer_steps = self.get_elements(_pypowsybl.ElementType.RATIO_TAP_CHANGER_STEP)
        return ratio_tap_changer_steps

    def get_phase_tap_changer_steps(self) -> pd.DataFrame:
        """ Get phase tap changer steps as a ``Pandas`` data frame.

        Returns:
            a phase tap changer steps data frame
        """
        phase_tap_changer_steps = self.get_elements(_pypowsybl.ElementType.PHASE_TAP_CHANGER_STEP)
        return phase_tap_changer_steps

    def get_ratio_tap_changers(self) -> pd.DataFrame:
        """ Create a ratio tap changers``Pandas`` data frame.

        Returns:
            the ratio tap changers data frame
        """
        ratio_tap_changers = self.get_elements(_pypowsybl.ElementType.RATIO_TAP_CHANGER)
        return ratio_tap_changers

    def get_phase_tap_changers(self) -> pd.DataFrame:
        """ Create a phase tap changers``Pandas`` data frame.

        Returns:
            the phase tap changers data frame
        """
        return self.get_elements(_pypowsybl.ElementType.PHASE_TAP_CHANGER)

    def get_reactive_capability_curve_points(self) -> pd.DataFrame:
        """ Get reactive capability curve points as a ``Pandas`` data frame.

        Returns:
            a reactive capability curve points data frame
        """
        reactive_capability_curve_points = self.get_elements(_pypowsybl.ElementType.REACTIVE_CAPABILITY_CURVE_POINT)
        if self.per_unit:
            reactive_capability_curve_points['p'] /= self.nominal_s
            reactive_capability_curve_points['min_q'] /= self.nominal_s
            reactive_capability_curve_points['max_q'] /= self.nominal_s
        return reactive_capability_curve_points

    def update_elements(self, element_type: _pypowsybl.ElementType, df: pd.DataFrame):
        """ Update network elements with a ``Pandas`` data frame for a specified element type.
        The data frame columns are mapped to IIDM element attributes and each row is mapped to an element using the
        index.

        Args:
            element_type (ElementType): the element type
            df (DataFrame): the ``Pandas`` data frame
        """
        for series_name in df.columns.values:
            series = df[series_name]
            series_type = _pypowsybl.get_series_type(element_type, series_name)
            if series_type == 2 or series_type == 3:
                _pypowsybl.update_network_elements_with_int_series(self._handle, element_type, series_name,
                                                                   df.index.values,
                                                                   series.values, len(series))
            elif series_type == 1:
                _pypowsybl.update_network_elements_with_double_series(self._handle, element_type, series_name,
                                                                      df.index.values,
                                                                      series.values, len(series))
            elif series_type == 0:
                _pypowsybl.update_network_elements_with_string_series(self._handle, element_type, series_name,
                                                                      df.index.values,
                                                                      series.values, len(series))
            else:
                raise PyPowsyblError(
                    f'Unsupported series type {series_type}, element type: {element_type}, series_name: {series_name}')

    def update_buses(self, df: pd.DataFrame):
        """ Update buses with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        if self.per_unit:
            df = pd.merge(df, self.get_buses()['voltage_level_id'],
                          left_index=True, right_index=True)
            df = pd.merge(df, self.get_voltage_levels()['nominal_v'], left_on='voltage_level_id', right_index=True)
            df['v_mag'] *= df['nominal_v']
            df = df.drop(['nominal_v', 'voltage_level_id'], axis=1)
        return self.update_elements(_pypowsybl.ElementType.BUS, df)

    def update_switches(self, df: pd.DataFrame):
        """ Update switches with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        return self.update_elements(_pypowsybl.ElementType.SWITCH, df)

    def update_generators(self, df: pd.DataFrame):
        """ Update generators with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        if self.per_unit:
            df = pd.merge(df, self.get_generators()['voltage_level_id'],
                          left_index=True, right_index=True)
            df = pd.merge(df, self.get_voltage_levels()['nominal_v'], left_on='voltage_level_id', right_index=True)
            df['target_v'] *= df['nominal_v']
            df['target_p'] *= self.nominal_s
            df['target_q'] *= self.nominal_s
            df = df.drop(['nominal_v', 'voltage_level_id'], axis=1)
        return self.update_elements(_pypowsybl.ElementType.GENERATOR, df)

    def update_loads(self, df: pd.DataFrame):
        """ Update loads with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        if self.per_unit:
            df['p0'] *= self.nominal_s
            df['q0'] *= self.nominal_s
        return self.update_elements(_pypowsybl.ElementType.LOAD, df)

    def update_batteries(self, df: pd.DataFrame):
        """ Update batteries with a ``Pandas`` data frame.

        Available columns names:
        - p0
        - q0
        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        if self.per_unit:
            df['p0'] *= self.nominal_s
            df['q0'] *= self.nominal_s
        return self.update_elements(_pypowsybl.ElementType.BATTERY, df)

    def update_dangling_lines(self, df: pd.DataFrame):
        """ Update dangling lines with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        if self.per_unit:
            df['p0'] *= self.nominal_s
            df['q0'] *= self.nominal_s
        return self.update_elements(_pypowsybl.ElementType.DANGLING_LINE, df)

    def update_vsc_converter_stations(self, df: pd.DataFrame):
        """ Update VSC converter stations with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        if self.per_unit:
            df['reactive_power_setpoint'] *= self.nominal_s
            df = pd.merge(df, self.get_vsc_converter_stations()['voltage_level_id'],
                          left_index=True, right_index=True)
            df = pd.merge(df, self.get_voltage_levels()['nominal_v'], left_on='voltage_level_id', right_index=True)
            df['voltage_setpoint'] *= df['nominal_v']
            df = df.drop(['nominal_v', 'voltage_level_id'], axis=1)
        return self.update_elements(_pypowsybl.ElementType.VSC_CONVERTER_STATION, df)

    def update_static_var_compensators(self, df: pd.DataFrame):
        """ Update static var compensators with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        if self.per_unit:
            df['reactive_power_setpoint'] *= self.nominal_s
            df = pd.merge(df, self.get_static_var_compensators()['voltage_level_id'],
                          left_index=True, right_index=True)
            df = pd.merge(df, self.get_voltage_levels()['nominal_v'], left_on='voltage_level_id', right_index=True)
            df['voltage_setpoint'] *= df['nominal_v']
            df = df.drop(['nominal_v', 'voltage_level_id'], axis=1)
        return self.update_elements(_pypowsybl.ElementType.STATIC_VAR_COMPENSATOR, df)

    def update_hvdc_lines(self, df: pd.DataFrame):
        """ Update HVDC lines with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        if self.per_unit:
            df['active_power_setpoint'] *= self.nominal_s
        return self.update_elements(_pypowsybl.ElementType.HVDC_LINE, df)

    def update_2_windings_transformers(self, df: pd.DataFrame):
        """ Update 2 windings transformers with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        return self.update_elements(_pypowsybl.ElementType.TWO_WINDINGS_TRANSFORMER, df)

    def update_ratio_tap_changers(self, df: pd.DataFrame):
        """ Update ratio tap changers with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        return self.update_elements(_pypowsybl.ElementType.RATIO_TAP_CHANGER, df)

    def update_phase_tap_changers(self, df: pd.DataFrame):
        """ Update phase tap changers with a ``Pandas`` data frame.

        Args:
            df (DataFrame): the ``Pandas`` data frame
        """
        return self.update_elements(_pypowsybl.ElementType.PHASE_TAP_CHANGER, df)

    def get_working_variant_id(self):
        """ The current working variant ID

        Returns:
            the id of the currently selected variant

        """
        return _pypowsybl.get_working_variant_id(self._handle)

    def clone_variant(self, src: str, target: str, may_overwrite=True):
        """ Creates a copy of the source variant

        Args:
            src: variant to copy
            target: id of the new variant that will be a copy of src
            may_overwrite: indicates if the target can be overwritten when it already exists
        """
        _pypowsybl.clone_variant(self._handle, src, target, may_overwrite)

    def set_working_variant(self, variant: str):
        """ Changes the working variant. The provided variant ID must correspond
        to an existing variant, for example created by a call to `clone_variant`.

        Args:
            variant: id of the variant selected (it must exist)
        """
        _pypowsybl.set_working_variant(self._handle, variant)

    def remove_variant(self, variant: str):
        """
        Removes a variant from the network.

        Args:
            variant: id of the variant to be deleted
        """
        _pypowsybl.remove_variant(self._handle, variant)

    def get_variant_ids(self):
        """
        Get the list of existing variant IDs.

        Returns:
            all the ids of the existing variants
        """
        return _pypowsybl.get_variant_ids(self._handle)


def create_empty(id: str = "Default") -> Network:
    """ Create an empty network.

    :param id: id of the network, defaults to 'Default'
    :type id: str, optional
    :return: an empty network
    :rtype: Network
    """
    return Network(_pypowsybl.create_empty_network(id))


def create_ieee9() -> Network:
    return Network(_pypowsybl.create_ieee_network(9))


def create_ieee14() -> Network:
    return Network(_pypowsybl.create_ieee_network(14))


def create_ieee30() -> Network:
    return Network(_pypowsybl.create_ieee_network(30))


def create_ieee57() -> Network:
    return Network(_pypowsybl.create_ieee_network(57))


def create_ieee118() -> Network:
    return Network(_pypowsybl.create_ieee_network(118))


def create_ieee300() -> Network:
    return Network(_pypowsybl.create_ieee_network(300))


def create_eurostag_tutorial_example1_network() -> Network:
    return Network(_pypowsybl.create_eurostag_tutorial_example1_network())


def _create_battery_network() -> Network:
    return Network(_pypowsybl.create_battery_network())


def _create_dangling_lines_network() -> Network:
    return Network(_pypowsybl.create_dangling_line_network())


def create_four_substations_node_breaker_network() -> Network:
    return Network(_pypowsybl.create_four_substations_node_breaker_network())


def get_import_formats() -> List[str]:
    """ Get list of supported import formats

    :return: the list of supported import formats
    :rtype: List[str]
    """
    return _pypowsybl.get_network_import_formats()


def get_export_formats() -> List[str]:
    """ Get list of supported export formats

    :return: the list of supported export formats
    :rtype: List[str]
    """
    return _pypowsybl.get_network_export_formats()


def get_import_parameters(format: str) -> pd.DataFrame:
    """ Get supported parameters infos for a given format

    :param format: the format
    :return: parameters infos
    :rtype: pd.DataFrame
    """
    series_array = _pypowsybl.create_importer_parameters_series_array(format)
    return create_data_frame_from_series_array(series_array)


def load(file: str, parameters: dict = {}) -> Network:
    """ Load a network from a file. File should be in a supported format.

    Args:
       file (str): a file
       parameters (dict, optional): a map of parameters

    Returns:
        a network
    """
    return Network(_pypowsybl.load_network(file, parameters))


def load_from_string(file_name: str, file_content: str, parameters: dict = {}) -> Network:
    """ Load a network from a string. File content should be in a supported format.

    Args:
       file_name (str): file name
       file_content (str): file content
       parameters (dict, optional): a map of parameters

    Returns:
        a network
    """
    return Network(_pypowsybl.load_network_from_string(file_name, file_content, parameters))
