/**
 * Copyright (c) 2021, RTE (http://www.rte-france.com)
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */
package com.powsybl.python;

import com.powsybl.commons.PowsyblException;
import com.powsybl.diff.LevelsData;
import com.powsybl.diff.NetworkDiffUtil;
import com.powsybl.iidm.network.Network;

import java.io.IOException;
import java.io.StringWriter;
import java.io.UncheckedIOException;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Paths;

/**
 * @author Christian Biasuzzi <christian.biasuzzi@soft.it>
 */
public final class DiffSingleLineDiagramUtil {

    public static final String DEFAULTLEVELSDATA = "{ \"levels\": [{\"id\": 1, \"i\": 0.1, \"v\": 0.1, \"c\": \"red\" }]}";
    static Double defaultThreshold = 0.0;
    static Double defaultVoltageThreshold = 0.0;

    private DiffSingleLineDiagramUtil() {
    }

    static void writeDiffSvg(Network network1, Network network2, String containerId, double pThreshold, double vThreshold, String levelsJson, String svgFile) {
        try (Writer writer = Files.newBufferedWriter(Paths.get(svgFile))) {
            LevelsData lds = getLevelsData(levelsJson);
            writeDiffSvg(network1, network2, containerId, pThreshold, vThreshold, lds, writer);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    private static LevelsData getLevelsData(String levelsJson) {
        return LevelsData.parseData((levelsJson == null || levelsJson.equals("") || levelsJson.trim().equals("")) ? DEFAULTLEVELSDATA : levelsJson);
    }

    static String getDiffSvg(Network network1, Network network2, String containerId, double pThreshold, double vThreshold, String levelsJson) {
        try (StringWriter writer = new StringWriter()) {
            LevelsData lds = getLevelsData(levelsJson);
            writeDiffSvg(network1, network2, containerId, pThreshold, vThreshold, lds, writer);
            writer.flush();
            return writer.toString();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    static void writeDiffSvg(Network network1, Network network2, String containerId, double pThreshold, double vThreshold, LevelsData levels, Writer writer) throws IOException {
        String diffSvg;
        if (network1.getVoltageLevel(containerId) != null) {
            diffSvg = new NetworkDiffUtil().getVoltageLevelSvgDiff(network1, network2, containerId,
                    pThreshold, vThreshold, levels);
        } else if (network1.getSubstation(containerId) != null) {
            diffSvg = new NetworkDiffUtil().getSubstationSvgDiff(network1, network2, containerId,
                    pThreshold, vThreshold, levels);
        } else {
            throw new PowsyblException("Container '" + containerId + "' not found");
        }
        writer.write(diffSvg);
        writer.flush();
    }

    static String getMergedDiffSvg(Network network1, Network network2, String containerId, double pThreshold, double vThreshold, String levelsJson, boolean showCurrent) {
        try (StringWriter writer = new StringWriter()) {
            LevelsData lds = getLevelsData(levelsJson);
            writeMergedDiffSvg(network1, network2, containerId, pThreshold, vThreshold, lds, showCurrent, writer);
            writer.flush();
            return writer.toString();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    static void writeMergedDiffSvg(Network network1, Network network2, String containerId, double pThreshold, double vThreshold, String levelsJson, boolean showCurrent, String svgFile) {
        try (Writer writer = Files.newBufferedWriter(Paths.get(svgFile))) {
            LevelsData lds = getLevelsData(levelsJson);
            writeMergedDiffSvg(network1, network2, containerId, pThreshold, vThreshold, lds, showCurrent, writer);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    static void writeMergedDiffSvg(Network network1, Network network2, String containerId, double pThreshold, double vThreshold, LevelsData levels, boolean showCurrent, Writer writer) throws IOException {
        String diffSvg;
        if (network1.getVoltageLevel(containerId) != null) {
            diffSvg = new NetworkDiffUtil().getVoltageLevelMergedSvgDiff(network1, network2, containerId,
                    pThreshold, vThreshold, levels, showCurrent);
        } else if (network1.getSubstation(containerId) != null) {
            diffSvg = new NetworkDiffUtil().getSubstationMergedSvgDiff(network1, network2, containerId,
                    pThreshold, vThreshold, levels, showCurrent);
        } else {
            throw new PowsyblException("Container '" + containerId + "' not found");
        }
        writer.write(diffSvg);
        writer.flush();
    }

}
