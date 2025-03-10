/**
 * Copyright (c) 2021, RTE (http://www.rte-france.com)
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */
package com.powsybl.python;

import com.powsybl.dataframe.DataframeMapper;
import com.powsybl.dataframe.DataframeMapperBuilder;
import com.powsybl.dataframe.impl.DefaultDataframeHandler;
import com.powsybl.dataframe.impl.Series;
import com.powsybl.iidm.import_.Importer;
import com.powsybl.iidm.parameters.Parameter;
import com.powsybl.iidm.parameters.ParameterType;
import com.powsybl.python.PyPowsyblApiHeader.ArrayPointer;
import com.powsybl.python.PyPowsyblApiHeader.SeriesPointer;
import com.powsybl.security.LimitViolation;
import com.powsybl.security.LimitViolationType;
import com.powsybl.security.SecurityAnalysisResult;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * Mappers to dataframes.
 *
 * @author Sylvain Leclerc <sylvain.leclerc at rte-france.com>
 */
public final class Dataframes {

    private static final DataframeMapper<Importer> PARAMETERS_MAPPER = new DataframeMapperBuilder<Importer, Parameter>()
        .itemsProvider(Importer::getParameters)
        .stringsIndex("name", Parameter::getName)
        .strings("description", Parameter::getDescription)
        .enums("type", ParameterType.class, Parameter::getType)
        .strings("default", p -> Objects.toString(p.getDefaultValue(), ""))
        .build();

    private static final DataframeMapper<SecurityAnalysisResult> BRANCH_RESULTS_MAPPER = createBranchResultsMapper();
    private static final DataframeMapper<SecurityAnalysisResult> T3WT_RESULTS_MAPPER = createThreeWindingsTransformersResults();
    private static final DataframeMapper<SecurityAnalysisResult> BUS_RESULTS_MAPPER = createBusResultsMapper();
    private static final DataframeMapper<SecurityAnalysisResult> LIMIT_VIOLATIONS_MAPPER = createLimitViolationsMapper();

    private Dataframes() {
    }

    /**
     * Maps an object to a C struct using the provided mapper.
     */
    public static <T> ArrayPointer<SeriesPointer> createCDataframe(DataframeMapper<T> mapper, T object) {
        CDataframeHandler handler = new CDataframeHandler();
        mapper.createDataframe(object, handler);
        return handler.getDataframePtr();
    }

    /**
     * Maps an object to java series
     */
    public static <T> List<Series> createSeries(DataframeMapper<T> mapper, T object) {
        List<Series> series = new ArrayList<>();
        mapper.createDataframe(object, new DefaultDataframeHandler(series::add));
        return List.copyOf(series);
    }

    /**
     * A mapper which maps an importer to a dataframe containing its parameters.
     */
    public static DataframeMapper<Importer> parametersMapper() {
        return PARAMETERS_MAPPER;
    }

    public static DataframeMapper<SecurityAnalysisResult> branchResultsMapper() {
        return BRANCH_RESULTS_MAPPER;
    }

    public static DataframeMapper<SecurityAnalysisResult> busResultsMapper() {
        return BUS_RESULTS_MAPPER;
    }

    public static DataframeMapper<SecurityAnalysisResult> threeWindingsTransformerResultsMapper() {
        return T3WT_RESULTS_MAPPER;
    }

    public static DataframeMapper<SecurityAnalysisResult> limitViolationsMapper() {
        return LIMIT_VIOLATIONS_MAPPER;
    }

    private static List<BranchResultContext> getBranchResults(SecurityAnalysisResult result) {
        List<BranchResultContext> branchResults = result.getPreContingencyResult()
            .getPreContingencyBranchResults().stream()
            .map(branchResult -> new BranchResultContext(branchResult, null))
            .collect(Collectors.toList());
        result.getPostContingencyResults().forEach(postContingencyResult -> {
            postContingencyResult.getBranchResults()
                .forEach(branchResult -> branchResults.add(new BranchResultContext(branchResult, postContingencyResult.getContingency().getId())));
        });
        return branchResults;
    }

    private static DataframeMapper<SecurityAnalysisResult> createBranchResultsMapper() {
        return new DataframeMapperBuilder<SecurityAnalysisResult, BranchResultContext>()
            .itemsProvider(Dataframes::getBranchResults)
            .stringsIndex("contingency_id", BranchResultContext::getContingencyId)
            .stringsIndex("branch_id", BranchResultContext::getBranchId)
            .doubles("p1", BranchResultContext::getP1)
            .doubles("q1", BranchResultContext::getQ1)
            .doubles("i1", BranchResultContext::getI1)
            .doubles("p2", BranchResultContext::getP2)
            .doubles("q2", BranchResultContext::getQ2)
            .doubles("i2", BranchResultContext::getI2)
            .build();
    }

    private static List<BusResultContext> getBusResults(SecurityAnalysisResult result) {
        List<BusResultContext> busResults = result.getPreContingencyResult()
            .getPreContingencyBusResults().stream()
            .map(busResult -> new BusResultContext(busResult, null))
            .collect(Collectors.toList());
        result.getPostContingencyResults().forEach(postContingencyResult -> {
            postContingencyResult.getBusResults()
                .forEach(busResult -> busResults.add(new BusResultContext(busResult, postContingencyResult.getContingency().getId())));
        });
        return busResults;
    }

    private static DataframeMapper<SecurityAnalysisResult> createBusResultsMapper() {
        return new DataframeMapperBuilder<SecurityAnalysisResult, BusResultContext>()
            .itemsProvider(Dataframes::getBusResults)
            .stringsIndex("contingency_id", BusResultContext::getContingencyId)
            .stringsIndex("voltage_level_id", BusResultContext::getVoltageLevelId)
            .stringsIndex("bus_id", BusResultContext::getBusId)
            .doubles("v_mag", BusResultContext::getV)
            .doubles("v_angle", BusResultContext::getAngle)
            .build();
    }

    private static List<ThreeWindingsTransformerResultContext> getThreeWindingsTransformerResults(SecurityAnalysisResult result) {
        List<ThreeWindingsTransformerResultContext> threeWindingsTransformerResults = result.getPreContingencyResult()
            .getPreContingencyThreeWindingsTransformerResults().stream()
            .map(threeWindingsTransformerResult -> new ThreeWindingsTransformerResultContext(threeWindingsTransformerResult, null))
            .collect(Collectors.toList());
        result.getPostContingencyResults().forEach(postContingencyResult -> {
            postContingencyResult.getThreeWindingsTransformerResult()
                .forEach(threeWindingsTransformerResult ->
                             threeWindingsTransformerResults.add(new ThreeWindingsTransformerResultContext(threeWindingsTransformerResult,
                                                                                                           postContingencyResult.getContingency().getId())));
        });
        return threeWindingsTransformerResults;
    }

    private static DataframeMapper<SecurityAnalysisResult> createThreeWindingsTransformersResults() {
        return new DataframeMapperBuilder<SecurityAnalysisResult, ThreeWindingsTransformerResultContext>()
            .itemsProvider(Dataframes::getThreeWindingsTransformerResults)
            .stringsIndex("contingency_id", ThreeWindingsTransformerResultContext::getContingencyId)
            .stringsIndex("transformer_id", ThreeWindingsTransformerResultContext::getThreeWindingsTransformerId)
            .doubles("p1", ThreeWindingsTransformerResultContext::getP1)
            .doubles("q1", ThreeWindingsTransformerResultContext::getQ1)
            .doubles("i1", ThreeWindingsTransformerResultContext::getI1)
            .doubles("p2", ThreeWindingsTransformerResultContext::getP2)
            .doubles("q2", ThreeWindingsTransformerResultContext::getQ2)
            .doubles("i2", ThreeWindingsTransformerResultContext::getI2)
            .doubles("p3", ThreeWindingsTransformerResultContext::getP3)
            .doubles("q3", ThreeWindingsTransformerResultContext::getQ3)
            .doubles("i3", ThreeWindingsTransformerResultContext::getI3)
            .build();
    }

    private static List<LimitViolationContext> getLimitViolations(SecurityAnalysisResult result) {
        List<LimitViolationContext> limitViolations = result.getPreContingencyResult().getLimitViolationsResult().getLimitViolations()
            .stream().map(limitViolation -> new LimitViolationContext("", limitViolation)).collect(Collectors.toList());
        result.getPostContingencyResults()
            .forEach(postContingencyResult -> limitViolations.addAll(postContingencyResult.getLimitViolationsResult()
                                                                         .getLimitViolations().stream()
                                                                         .map(limitViolation -> new LimitViolationContext(postContingencyResult.getContingency().getId(), limitViolation))
                                                                         .collect(Collectors.toList())));
        return limitViolations;
    }

    private static DataframeMapper<SecurityAnalysisResult> createLimitViolationsMapper() {
        return new DataframeMapperBuilder<SecurityAnalysisResult, LimitViolationContext>()
            .itemsProvider(Dataframes::getLimitViolations)
            .stringsIndex("contingency_id", LimitViolationContext::getContingencyId)
            .stringsIndex("subject_id", LimitViolation::getSubjectId)
            .strings("subject_name", p -> Objects.toString(p.getSubjectName(), ""))
            .enums("limit_type", LimitViolationType.class, LimitViolation::getLimitType)
            .strings("limit_name", p -> Objects.toString(p.getLimitName(), ""))
            .doubles("limit", LimitViolation::getLimit)
            .ints("acceptable_duration", LimitViolation::getAcceptableDuration)
            .doubles("limit_reduction", LimitViolation::getLimitReduction)
            .doubles("value", LimitViolation::getValue)
            .strings("side", p -> Objects.toString(p.getSide(), ""))
            .build();
    }
}
