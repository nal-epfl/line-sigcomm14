/*
 *	Copyright (C) 2014 Ovidiu Mara
 *
 *	This program is free software; you can redistribute it and/or modify
 *	it under the terms of the GNU General Public License as published by
 *	the Free Software Foundation; version 2 is the only version of this
 *  license which this program may be distributed under.
 *
 *	This program is distributed in the hope that it will be useful,
 *	but WITHOUT ANY WARRANTY; without even the implied warranty of
 *	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *	GNU General Public License for more details.
 *
 *	You should have received a copy of the GNU General Public License
 *	along with this program; if not, write to the Free Software
 *	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/

#include "result_processing.h"

#include <QtCore>

#include "intervalmeasurements.h"
#include "netgraph.h"
#include "run_experiment_params.h"
#include "tomodata.h"

bool processResults(QString paramsFileName,
                    quint64 resamplePeriod,
                    qreal binSize,
                    bool perFlowAnalysis);

bool processResults(QString workingDir,
                    QString graphName,
                    QString experimentSuffix,
                    quint64 resamplePeriod,
                    qreal binSize,
                    qreal lossThreshold,
                    int numResamplings,
                    qreal gapThreshold,
                    bool perFlowAnalysis);

QString guessGraphName(QString workingDir) {
    QString simulationText;
    if (!readFile(workingDir + "/" + "simulation.txt", simulationText)) {
        return QString();
    }
    foreach (QString line, simulationText.split("\n")) {
        QStringList tokens = line.split("=");
        if (tokens.count() == 2) {
            if (tokens[0] == "graph") {
                return tokens[1];
            }
        }
    }
    return QString();
}

QString guessExperimentSuffix(QString workingDir) {
    // quad.2014.04.14.17.43.46.418114995566664.1118666809-link-100Mbps-pareto-1Mb-pareto-1Mb-policing-1.0-0.3-buffers-large-none-1-drop-tail-rtt-48-120
    workingDir = workingDir.split("/").last();
    if (workingDir.contains("-")) {
        workingDir = workingDir.mid(workingDir.indexOf('-') + 1);
        return workingDir;
    }
    return "";
}

bool processResults(QString paramsFileName,
                    quint64 resamplePeriod, qreal binSize,
                    qreal lossThreshold,
                    int numResamplings,
                    qreal gapThreshold,
                    bool perFlowAnalysis) {
    QString workingDir;
    QString graphName;
    QString experimentSuffix;

	RunParams runParams;
	if (!loadRunParams(runParams, paramsFileName)) {
        workingDir = paramsFileName;
        graphName = guessGraphName(workingDir);
        experimentSuffix = guessExperimentSuffix(workingDir);

        if (graphName.isEmpty() || experimentSuffix.isEmpty()) {
            return false;
        }
    } else {
        workingDir = runParams.workingDir;
        graphName = runParams.graphName;
        experimentSuffix = runParams.experimentSuffix;
    }

    qDebug() << QString("Exporting results for graph %1, working dir %2, suffix %3")
                .arg(graphName)
                .arg(workingDir)
                .arg(experimentSuffix);

    return processResults(workingDir, graphName, experimentSuffix,
                          resamplePeriod, binSize,
                          lossThreshold,
                          numResamplings,
                          gapThreshold,
                          perFlowAnalysis);
}

bool loadGraph(QString workingDir, QString graphName, NetGraph &g)
{
    // Remove path
    if (graphName.contains("/")) {
        graphName = graphName.mid(graphName.lastIndexOf("/") + 1);
    }
    // Add extension
    if (!graphName.endsWith(".graph"))
        graphName += ".graph";
    // Add path
    g.setFileName(workingDir + "/" + graphName);
    if (!g.loadFromFile()) {
        return false;
    }
    return true;
}

bool computePathCongestionProbabilities(QString workingDir, QString graphName, QString experimentSuffix, quint64 resamplePeriod)
{
    NetGraph g;
    if (!loadGraph(workingDir, graphName, g))
        return false;

    QVector<int> pathTrafficClass = g.getPathTrafficClassStrict(true);

    QList<qreal> thresholds = QList<qreal>()
                              << 0.100  // 10 % = 1/10
                              << 0.050
                              << 0.040
                              << 0.030
                              << 0.025
                              << 0.020
                              << 0.015
                              << 0.010  // 1 % = 1/100
                              << 0.005
                              << 0.0025
                              << 0.0010  // 0.1 % = 1/1k
                              << 0.0005
                              << 0.00025
                              << 0.00020
                              << 0.00015
                              << 0.000010  // 0.001 % = 1/100k
                              << 0.000001;  // 0.0001 % = 1/M

    // 1st index: threshold
    // 2nd index: path
    QVector<QVector<qreal> > pathCongestionProbabilities;

    ExperimentIntervalMeasurements experimentIntervalMeasurements;
    if (!experimentIntervalMeasurements.load(workingDir + "/" + "interval-measurements.data")) {
        return false;
    }

    experimentIntervalMeasurements = experimentIntervalMeasurements.resample(resamplePeriod);

    Q_ASSERT_FORCE(experimentIntervalMeasurements.numPaths == g.paths.count());

    foreach (qreal threshold, thresholds) {
        QVector<qreal> pathCongestionProbByThreshold;
        for (int p = 0; p < experimentIntervalMeasurements.numPaths; p++) {
            qreal congestionProbability = 0;
            int numIntervals = 0;
            const qreal firstTransientCutSec = 10;
            const qreal lastTransientCutSec = 10;
            const int firstTransientCut = firstTransientCutSec * 1.0e9 / experimentIntervalMeasurements.intervalSize;
            const int lastTransientCut = lastTransientCutSec * 1.0e9 / experimentIntervalMeasurements.intervalSize;
            for (int interval = firstTransientCut; interval < experimentIntervalMeasurements.numIntervals() - lastTransientCut; interval++) {
                bool ok;
                qreal loss = 1.0 - experimentIntervalMeasurements.intervalMeasurements[interval].pathMeasurements[p].successRate(&ok);
                if (!ok)
                    continue;
                numIntervals++;
                if (loss >= threshold) {
                    congestionProbability += 1.0;
                }
            }
            congestionProbability /= qMax(1, numIntervals);
            pathCongestionProbByThreshold.append(congestionProbability);
        }
        pathCongestionProbabilities.append(pathCongestionProbByThreshold);
    }

    // save result

    QString dataFile;
    dataFile += "Experiment\t" + experimentSuffix + "\n";
    for (int t = -2; t < thresholds.count(); t++) {
        if (t == -2) {
            dataFile += "Path";
        } else if (t == -1) {
            dataFile += "Class";
        } else {
            dataFile += QString("%1").arg(thresholds[t] * 100.0);
        }
        for (int p = 0; p < experimentIntervalMeasurements.numPaths; p++) {
            if (pathTrafficClass[p] < 0)
                continue;
            if (t == -2) {
                dataFile += QString("\tP%1").arg(p + 1);
            } else if (t == -1) {
                dataFile += QString("\t%1").arg(pathTrafficClass[p]);
            } else {
                dataFile += QString("\t%1").arg(pathCongestionProbabilities[t][p] * 100.0, 0, 'f', 2);
            }
        }
        dataFile += "\n";
    }
    if (!saveFile(workingDir + "/" + "path-congestion-probs.txt", dataFile))
        return false;

    return true;
}

bool dumpPathIntervalData(QString workingDir, QString graphName, QString experimentSuffix, quint64 resamplePeriod)
{
    NetGraph g;
    if (!loadGraph(workingDir, graphName, g))
        return false;

    QVector<int> pathTrafficClass = g.getPathTrafficClassStrict(true);

    // 1st index: interval
    // 2nd index: path
    QVector<QVector<qreal> > pathLossRates;

    ExperimentIntervalMeasurements experimentIntervalMeasurements;
    if (!experimentIntervalMeasurements.load(workingDir + "/" + "interval-measurements.data")) {
        return false;
    }

    experimentIntervalMeasurements = experimentIntervalMeasurements.resample(resamplePeriod);

    Q_ASSERT_FORCE(experimentIntervalMeasurements.numPaths == g.paths.count());

    for (int i = 0; i < experimentIntervalMeasurements.numIntervals(); i++) {
        QVector<qreal> pathLossRatesForInterval;
        for (int p = 0; p < experimentIntervalMeasurements.numPaths; p++) {
            qreal loss = 1.0 - experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p].successRate();
            pathLossRatesForInterval.append(loss);
        }
        pathLossRates.append(pathLossRatesForInterval);
    }

    // save result

    QString dataFile;
    dataFile += "Experiment\t" + experimentSuffix + "\n";
    for (int i = -2; i < experimentIntervalMeasurements.numIntervals(); i++) {
        if (i == -2) {
            dataFile += "Path";
        } else if (i == -1) {
            dataFile += "Class";
        } else {
            dataFile += QString("%1").arg(i);
        }
        for (int p = 0; p < experimentIntervalMeasurements.numPaths; p++) {
            if (pathTrafficClass[p] < 0)
                continue;
            if (i == -2) {
                dataFile += QString("\tP%1").arg(p + 1);
            } else if (i == -1) {
                dataFile += QString("\t%1").arg(pathTrafficClass[p]);
            } else {
                dataFile += QString("\t%1").arg(pathLossRates[i][p] * 100.0, 0, 'f', 2);
            }
        }
        dataFile += "\n";
    }
    if (!saveFile(workingDir + "/" + "path-interval-data.txt", dataFile))
        return false;

    return true;
}

const int minNumPackets = 10;

qreal distance(QList<qreal> cluster1, QList<qreal> cluster2)
{
    qreal sum = 0;
    qreal count = 0;
    foreach (qreal v1, cluster1) {
        foreach (qreal v2, cluster2) {
            sum += v2 - v1;
            count += 1;
        }
    }
    sum /= qMax(1.0, count);
    return sum;
}

#define USE_INTERVAL_MASK 0
#define LINK_USE_INTERVAL_MASK 0

// Analysis of per-link data
bool nonNeutralityAnalysis(QString workingDir, QString graphName, QString experimentSuffix,
                           quint64 resamplePeriod,
                           qreal binSize,
                           qreal lossThreshold,
                           bool perFlowAnalysis)
{
    const qreal gapThreshold = 33.0 / 100.0;

    NetGraph g;
    if (!loadGraph(workingDir, graphName, g))
        return false;
    g.flattenConnections();

    QVector<int> pathTrafficClass = !perFlowAnalysis ? g.getPathTrafficClassStrict(true)
                                                     : g.getConnectionTrafficClass();

    ExperimentIntervalMeasurements experimentIntervalMeasurements;
    if (!experimentIntervalMeasurements.load(workingDir + "/" +
                                             ( !perFlowAnalysis
                                             ? "interval-measurements.data"
                                             : "flow-interval-measurements.data"))) {
        return false;
    }

    experimentIntervalMeasurements = experimentIntervalMeasurements.resample(resamplePeriod);

    Q_ASSERT_FORCE(experimentIntervalMeasurements.numEdges == g.edges.count());
    Q_ASSERT_FORCE(experimentIntervalMeasurements.numPaths == !perFlowAnalysis ? g.paths.count()
                                                                               : g.connections.count());

    const qreal firstTransientCutSec = 10;
    const qreal lastTransientCutSec = 10;
    const int firstTransientCut = firstTransientCutSec * 1.0e9 / experimentIntervalMeasurements.intervalSize;
    const int lastTransientCut = lastTransientCutSec * 1.0e9 / experimentIntervalMeasurements.intervalSize;

    // first index: edge
    // second index (key): bin + class
    // third index: arbitrary path index
    QList<QHash<QString, QList<qreal> > > edgeClassPathCongProbs;
    QList<QSet<QString> > edgeBins;
    for (int e = 0; e < experimentIntervalMeasurements.numEdges; e++) {
        edgeClassPathCongProbs << QHash<QString, QList<qreal> >();
        edgeBins << QSet<QString>();

        QVector<bool> intervalMask;
        intervalMask.fill(false, experimentIntervalMeasurements.numIntervals());
        for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
            intervalMask[i] = true;
            if (USE_INTERVAL_MASK || LINK_USE_INTERVAL_MASK) {
                for (int p = 0; p < experimentIntervalMeasurements.numPaths; p++) {
                    QInt32Pair ep = QInt32Pair(e, p);
                    if (experimentIntervalMeasurements.globalMeasurements.perPathEdgeMeasurements[ep].numPacketsInFlight == 0)
                        continue;
                    if (experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep].numPacketsInFlight < minNumPackets) {
                        intervalMask[i] = false;
                        break;
                    }
                }
            }
        }

        for (int p = 0; p < experimentIntervalMeasurements.numPaths; p++) {
            QInt32Pair ep = QInt32Pair(e, p);
            if (experimentIntervalMeasurements.globalMeasurements.perPathEdgeMeasurements[ep].numPacketsInFlight == 0)
                continue;

            qreal congestionProbability = 0;
            int numIntervals = 0;
            qreal ppi = 0;
            for (int interval = firstTransientCut; interval < experimentIntervalMeasurements.numIntervals() - lastTransientCut; interval++) {
                if (!intervalMask[interval])
                    continue;
                bool ok;
                qreal loss = 1.0 -
                             experimentIntervalMeasurements.intervalMeasurements[interval].perPathEdgeMeasurements[ep].successRate(&ok);
                if (!ok)
                    continue;
                if (experimentIntervalMeasurements.intervalMeasurements[interval].perPathEdgeMeasurements[ep].numPacketsInFlight < minNumPackets)
                    continue;
                numIntervals++;
                if (loss >= lossThreshold) {
                    congestionProbability += 1.0;
                }
                ppi += experimentIntervalMeasurements.intervalMeasurements[interval].perPathEdgeMeasurements[ep].numPacketsInFlight;
            }
            congestionProbability /= qMax(1, numIntervals);
            ppi /= qMax(1, numIntervals);

            int bin = 1 + int(ppi / binSize);

            edgeClassPathCongProbs[e][QString("b%1c%2").arg(bin).arg(1 + pathTrafficClass[p])] << congestionProbability;
            edgeBins[e].insert(QString("b%1").arg(bin));
        }
    }

    // Detection
    QList< QList<qreal> > edgeNeutralClues;
    QList< QList<qreal> > edgeNonNeutralClues;
    QList< QString > edgeDetectedNeutrality;
    QList< QString > edgeDetectionResult;
    for (int e = 0; e < experimentIntervalMeasurements.numEdges; e++) {
        edgeNeutralClues << QList<qreal>();
        edgeNonNeutralClues << QList<qreal>();
        foreach (QString bin, edgeBins[e]) {
            QString bc1 = QString("%1c1").arg(bin);
            QString bc2 = QString("%1c2").arg(bin);
            if (!edgeClassPathCongProbs[e].contains(bc1) || !edgeClassPathCongProbs[e].contains(bc2))
                continue;
            qreal d = fabs(distance(edgeClassPathCongProbs[e][bc1], edgeClassPathCongProbs[e][bc2]));
            qreal reference = qMax(0.01, qMax(median(edgeClassPathCongProbs[e][bc1]), median(edgeClassPathCongProbs[e][bc2])));
            if (d < reference * gapThreshold) {
                edgeNeutralClues[e] << d / reference;
            } else {
                edgeNonNeutralClues[e] << d / reference;
            }
        }
        if (edgeNeutralClues[e].isEmpty() && edgeNonNeutralClues[e].isEmpty()) {
            edgeDetectedNeutrality << "undecidable";
            edgeDetectionResult << "undecidable";
        } else if (!edgeNeutralClues[e].isEmpty() && edgeNonNeutralClues[e].isEmpty()) {
            edgeDetectedNeutrality << "neutral (strong)";
            edgeDetectionResult << (g.edges[e].isNeutral() ? "true negative" : "false negative");
        } else if (edgeNeutralClues[e].isEmpty() && !edgeNonNeutralClues[e].isEmpty()) {
            edgeDetectedNeutrality << "non-neutral (strong)";
            edgeDetectionResult << (g.edges[e].isNeutral() ? "false positive" : "true positive");
        } else if (sum(edgeNeutralClues[e]) > sum(edgeNonNeutralClues[e])) {
            edgeDetectedNeutrality << "neutral (weak)";
            edgeDetectionResult << (g.edges[e].isNeutral() ? "true negative" : "false negative");
        } else {
            edgeDetectedNeutrality << "non-neutral (weak)";
            edgeDetectionResult << (g.edges[e].isNeutral() ? "false positive" : "true positive");
        }
    }

    // save txt report
    QString dataFile;
    dataFile += QString("Experiment\t%1\tinterval\t%2\n").arg(experimentSuffix).arg(experimentIntervalMeasurements.intervalSize / 1.0e9);
    dataFile += "\n";
    for (int e = 0; e < experimentIntervalMeasurements.numEdges; e++) {
        dataFile += QString("Link\t%1\t%2").arg(e + 1).arg(g.edges[e].isNeutral() ? "neutral" : g.edges[e].policerCount > 1 ? "policing" : "shaping");
        dataFile += "\n";
        foreach (QString c, sorted(edgeClassPathCongProbs[e].uniqueKeys())) {
            dataFile += QString("Class\t%1").arg(c);
            foreach (qreal prob, edgeClassPathCongProbs[e][c]) {
                dataFile += QString("\t%1").arg(prob * 100.0);
            }
            dataFile += "\n";
        }

        dataFile += QString("Neutral clues");
        foreach (qreal c, edgeNeutralClues[e]) {
            dataFile += QString("\t%1").arg(c * 100.0);
        }
        dataFile += "\n";

        dataFile += QString("Non-neutral clues");
        foreach (qreal c, edgeNonNeutralClues[e]) {
            dataFile += QString("\t%1").arg(c * 100.0);
        }
        dataFile += "\n";

        dataFile += QString("Detection\t%1\n").arg(edgeDetectedNeutrality[e]);
        dataFile += QString("Result\t%1\n").arg(edgeDetectionResult[e]);

        dataFile += "\n";
    }
    if (!saveFile(workingDir + "/" +
                  QString("link-analysis-%1-%2-lossth-%3.txt")
                  .arg(experimentSuffix)
                  .arg(timeToString(experimentIntervalMeasurements.intervalSize))
                  .arg(lossThreshold),
                  dataFile))
        return false;

    // save html report
    QString nonNeutralLinksStr;
    for (qint32 e = 0; e < g.edges.count(); e++) {
        if (!g.edges[e].isNeutral()) {
            nonNeutralLinksStr += QString(nonNeutralLinksStr.isEmpty() ? "" : ", ") + QString("%1").arg(e + 1);
        }
    }

    QHash<int, QSet<QString> > class2traffic;
    foreach (NetGraphConnection c, g.connections) {
        class2traffic[c.trafficClass].insert(c.encodedType);
    }
    QString htmlTraffic;
    foreach (int c, sorted(class2traffic.uniqueKeys())) {
        htmlTraffic += QString("      <li>Traffic for class %1:").arg(c + 1);
        foreach (QString traffic, class2traffic[c]) {
            htmlTraffic += QString("%1%2")
                           .arg(htmlTraffic.endsWith(":") ? "" : ", ")
                           .arg(traffic);
        }
        htmlTraffic += QString("</li>\n");
    }

    QString html;
    html = QString("<!DOCTYPE html>\n"
                   "<html>\n"
                   "<head>\n"
                   "  <meta charset=\"UTF-8\">\n"
                   "  <title>Neutrality Project Plan</title>\n"
				   "  <link rel=\"shortcut icon\" type=\"image/png\" href=\"../../../html/plan.png\">\n"
				   "  <link rel=\"stylesheet\" href=\"../../../html/style.css\">\n"
                   "</head>\n"
                   "<body>\n"
                   "<div class=\"section\">\n"
                   "  <h2>Experiment: %1</h2>\n"
				   "  <img src=\"../../../html/pegasus.png\"></img>\n"
                   "  <p>Experiment parameters:\n"
                   "    <ul>\n"
                   "      <li>Non-neutral links: %2</li>\n"
                   "%3"
                   "      <li>Interval size: %4</li>\n"
                   "    </ul>\n"
                   "  </p>\n"
                   "  <div class=\"section\">\n"
                   "    <h3>Real link congestion probabilities:</h3>\n")
           .arg(experimentSuffix)
           .arg(nonNeutralLinksStr)
           .arg(htmlTraffic)
           .arg(timeToString(experimentIntervalMeasurements.intervalSize));

    html += QString("    <table>\n"
                    "    <tbody>\n"
                    "      <tr>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Link</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Type</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Result</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Prob. cong. for class 1 (%, real)</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Prob. cong. for class 2 (%, real)</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Gaps indicating neutrality</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Gaps indicating non-neutrality</th>\n"
                    "      </tr>\n");

    for (int e = 0; e < experimentIntervalMeasurements.numEdges; e++) {
        if (edgeDetectionResult[e].contains("undecidable"))
            continue;

        html += QString("      <tr>\n");

        // link
        html += QString("      <td>");
        html += QString("%1 ").arg(e + 1);
        html += QString("      </td>\n");

        // type
        html += QString("      <td nowrap>");
        html += (g.edges[e].isNeutral() ? "neutral" : "non-neutral");
        html += QString("      </td>\n");

        // result
        html += QString("      <td nowrap style=\"background-color:%1\">")
                .arg(edgeDetectionResult[e].contains("false") ?
                         "#f99" :
                         edgeDetectionResult[e].contains("positive") ?
                             "#9f9" :
                             edgeDetectionResult[e].contains("undecidable") ?
                                 "#ff9" :
                                 "#fff");
        html += edgeDetectionResult[e];
        html += QString("      </td>\n");

        // class 1 real
        html += QString("      <td>");
        foreach (QString classBin, sorted(edgeClassPathCongProbs[e].uniqueKeys())) {
            if (classBin.endsWith("1")) {
                html += QString("%1:").arg(classBin);
                foreach (qreal prob, edgeClassPathCongProbs[e][classBin]) {
                    html += QString("%1%2").arg(html.endsWith(":") ? " " : ", ").arg(prob * 100.0);
                }
                html += "<br/>";
            }
        }
        html += QString("      </td>\n");

        // class 2 real
        html += QString("      <td>");
        foreach (QString classBin, sorted(edgeClassPathCongProbs[e].uniqueKeys())) {
            if (classBin.endsWith("2")) {
                html += QString("%1:").arg(classBin);
                foreach (qreal prob, edgeClassPathCongProbs[e][classBin]) {
                    html += QString("%1%2").arg(html.endsWith(":") ? " " : ", ").arg(prob * 100.0);
                }
                html += "<br/>";
            }
        }
        html += QString("      </td>\n");

        // neutral clues
        html += QString("      <td>");
        foreach (qreal c, edgeNeutralClues[e]) {
            html += QString("%1%2").arg(html.endsWith(">") ? "" : ", ").arg(c * 100.0);
        }
        html += QString("      </td>\n");

        // non-neutral clues
        html += QString("      <td>");
        foreach (qreal c, edgeNonNeutralClues[e]) {
            html += QString("%1%2").arg(html.endsWith(">") ? "" : ", ").arg(c * 100.0);
        }
        html += QString("      </td>\n");

        html += QString("      </tr>\n");
    }
    html += QString("    </tbody>\n"
                    "    </table>\n");

    int truePositives = 0;
    int falsePositives = 0;
    int totalNonNeutral = 0;
    int trueNegatives = 0;
    int falseNegatives = 0;
    int totalNeutral = 0;
    for (int e = 0; e < experimentIntervalMeasurements.numEdges; e++) {
        if (edgeDetectionResult[e] == "undecidable")
            continue;
        if (g.edges[e].isNeutral()) {
            totalNeutral++;
        } else {
            totalNonNeutral++;
        }
        if (edgeDetectionResult[e] == "true positive") {
            truePositives++;
        } else if (edgeDetectionResult[e] == "true negative") {
            trueNegatives++;
        } else if (edgeDetectionResult[e] == "false negative") {
            falseNegatives++;
        } else if (edgeDetectionResult[e] == "false positive") {
            falsePositives++;
        }
    }

    html += QString("    <p>True positives: %1 / %2 = %3 %</p>\n")
            .arg(truePositives)
            .arg(totalNonNeutral)
            .arg(truePositives * 100.0 / qMax(totalNonNeutral, 1));

    html += QString("    <p>True negatives: %1 / %2 = %3 %</p>\n")
            .arg(trueNegatives)
            .arg(totalNeutral)
            .arg(trueNegatives * 100.0 / qMax(totalNeutral, 1));

    html += QString("    <p>False positives: %1 / %2 = %3 %</p>\n")
            .arg(falsePositives)
            .arg(totalNeutral)
            .arg(falsePositives * 100.0 / qMax(totalNeutral, 1));

    html += QString("    <p>False negatives: %1 / %2 = %3 %</p>\n")
            .arg(falseNegatives)
            .arg(totalNonNeutral)
            .arg(falseNegatives * 100.0 / qMax(totalNonNeutral, 1));

    html += QString("  </div>\n"
                    "</div>\n"
					"<script src=\"../../../html/todo.js\"></script>\n"
					"<script src=\"../../../html/toc.js\"></script>\n"
                    "</body>\n"
                    "</html>\n");

    if (!saveFile(workingDir + "/" +
                  QString("link-analysis-%1-%2-lossth-%3.html")
                  .arg(experimentSuffix)
                  .arg(timeToString(experimentIntervalMeasurements.intervalSize))
                  .arg(lossThreshold),
                  html))
        return false;

    QDir::setCurrent(workingDir);
	QProcess::execute("../../../plotting-scripts-new/plot-edge-class-path-cong-prob.py",
                      QStringList()
                      << "--in"
                      << QString("link-analysis-%1-%2-lossth-%3.txt")
                      .arg(experimentSuffix)
                      .arg(timeToString(experimentIntervalMeasurements.intervalSize))
                      .arg(lossThreshold)
                      << "--out"
                      << QString("link-analysis-%1").arg(lossThreshold, 0, 'f', 2));

    return true;
}

// Analysis of end-to-end data
bool nonNeutralityDetection(QString workingDir, QString graphName, QString experimentSuffix, quint64 resamplePeriod,
                            qreal binSize,
                            qreal lossThreshold,
                            int numSamplingIterations,
                            qreal gapThreshold,
                            bool perFlowAnalysis)
{
    bool diagnostic = true;

    // natural indices
    QSet<qint32> backgroundHosts = graphName == "pegasus"
                                   ? (QList<qint32>() << 29 << 30 << 31 << 32 << 33 << 34).toSet()
                                   : QSet<qint32>();

    NetGraph g;
    if (!loadGraph(workingDir, graphName, g))
        return false;
    g.flattenConnections();

    QVector<int> pathTrafficClass = !perFlowAnalysis ? g.getPathTrafficClassStrict(true)
                                                     : g.getConnectionTrafficClass();

    QVector<qint32> connection2path = g.getConnection2PathMapping();
    foreach (qint32 p, connection2path) {
        Q_ASSERT_FORCE(p >= 0);
    }

    ExperimentIntervalMeasurements experimentIntervalMeasurements;
    if (!experimentIntervalMeasurements.load(workingDir + "/" +
                                             ( !perFlowAnalysis
                                             ? "interval-measurements.data"
                                             : "flow-interval-measurements.data"))) {
        return false;
    }

    experimentIntervalMeasurements = experimentIntervalMeasurements.resample(resamplePeriod);

    Q_ASSERT_FORCE(experimentIntervalMeasurements.numEdges == g.edges.count());
    Q_ASSERT_FORCE(experimentIntervalMeasurements.numPaths == !perFlowAnalysis ? g.paths.count()
                                                                               : g.connections.count());

    for (int p = 0; p < experimentIntervalMeasurements.numPaths; p++) {
        for (int i = 0; i < experimentIntervalMeasurements.numIntervals(); i++) {
            const LinkIntervalMeasurement &pathMeasurements = experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p];
            //Q_ASSERT_FORCE(pathMeasurements.numPacketsInFlight == (qint64)pathMeasurements.events.count());
            QVector<quint8> bits = pathMeasurements.events.toVector();
            //Q_ASSERT_FORCE(bits.count(0) == pathMeasurements.numPacketsDropped);
        }
    }

    const qreal firstTransientCutSec = 10;
    const qreal lastTransientCutSec = 10;
    const int firstTransientCut = firstTransientCutSec * 1.0e9 / experimentIntervalMeasurements.intervalSize;
    const int lastTransientCut = lastTransientCutSec * 1.0e9 / experimentIntervalMeasurements.intervalSize;

    QHash<QSet<qint32>, bool> linkSequence2neutrality;
    QHash<QSet<qint32>, bool> linkSequence2pathPair11;
    QHash<QSet<qint32>, bool> linkSequence2pathPair22;
    // first key: link sequence
    // second key: class&bin
    // value: list of probs of congestion
    QHash<QSet<qint32>, QHash<QString, QList<qreal> > > linkSequence2ClassBin2computedProbsCongestion;
    QHash<QSet<qint32>, QHash<QString, QList<qreal> > > linkSequence2ClassBin2trueProbsCongestion;
    QHash<QSet<qint32>, QSet<QString> > linkSequence2Bins;

    // first index: link
    // second index: interval
    QVector<QVector<bool> > linkIntervalMask;
    linkIntervalMask.resize(experimentIntervalMeasurements.numEdges);
    for (int e = 0; e < experimentIntervalMeasurements.numEdges; e++) {
        linkIntervalMask[e].fill(false, experimentIntervalMeasurements.numIntervals());
        for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
            linkIntervalMask[e][i] = true;
            if (USE_INTERVAL_MASK) {
                bool foundOne = false;
                for (int p = 0; p < experimentIntervalMeasurements.numPaths; p++) {
                    QInt32Pair ep = QInt32Pair(e, p);
                    // It's OK to use this, it's essentially checking the routing matrix. Not cheating.
                    if (experimentIntervalMeasurements.globalMeasurements.perPathEdgeMeasurements[ep].numPacketsInFlight == 0)
                        continue;
                    // This is not OK to do (cheating), wo we won't do it; keep the code here for checking:
                    //if (experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep].numPacketsInFlight < minNumPackets) {
                    // This is OK to do (use end-to-end data):
                    if (experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p].numPacketsInFlight < minNumPackets) {
                        linkIntervalMask[e][i] = false;
                        break;
                    } else {
                        foundOne = true;
                    }
                }
                if (!foundOne) {
                    linkIntervalMask[e][i] = false;
                }
            }
        }
    }
    // first key: link sequence
    // second index: interval
    QHash<QSet<qint32>, QVector<bool> > linkSequence2IntervalMask;
    // value: min(each path's ppi)
    QHash<QSet<qint32>, QVector<int> > linkSequence2PPI;
    QHash<QSet<qint32>, QSet<QPair<qint32, qint32> > > linkSequence2PathPairs;
    QHash<QSet<qint32>, QSet<qint32> > linkSequence2Paths;
    QHash<QSet<qint32>, QList<qint32> > linkSequence2OrderedLinkSequence;

    // Compute linkSequence2PPI
    for (int p1 = 0; p1 < experimentIntervalMeasurements.numPaths; p1++) {
        const NetGraphPath &path1 = !perFlowAnalysis ? g.paths[p1] : g.paths[connection2path[p1]];
        if (backgroundHosts.contains(path1.source + 1) || backgroundHosts.contains(path1.dest + 1))
            continue;
        for (int p2 = p1 + 1; p2 < experimentIntervalMeasurements.numPaths; p2++) {
            const NetGraphPath &path2 = !perFlowAnalysis ? g.paths[p2] : g.paths[connection2path[p2]];
            if (backgroundHosts.contains(path2.source + 1) || backgroundHosts.contains(path2.dest + 1))
                continue;
            QSet<NetGraphEdge> commonEdges = path1.edgeSet;
            commonEdges.intersect(path2.edgeSet);
            if (commonEdges.isEmpty())
                continue;
            QSet<qint32> linkSequence;
            foreach (NetGraphEdge edge, commonEdges) {
                linkSequence.insert(edge.index);
            }
            if (!linkSequence2OrderedLinkSequence.contains(linkSequence)) {
                linkSequence2OrderedLinkSequence[linkSequence].clear();
                foreach (NetGraphEdge edge, path1.edgeList) {
                    if (commonEdges.contains(edge)) {
                        linkSequence2OrderedLinkSequence[linkSequence] << edge.index;
                    }
                }
            }

            // linkSequence2neutrality
            bool neutrality = true;
            foreach (NetGraphEdge edge, commonEdges) {
                neutrality = neutrality && edge.isNeutral();
            }
            linkSequence2neutrality[linkSequence] = neutrality;
            // linkSequence2Paths
            linkSequence2PathPairs[linkSequence].insert(QInt32Pair(p1, p2));
            linkSequence2Paths[linkSequence].insert(p1);
            linkSequence2Paths[linkSequence].insert(p2);
            // linkSequence2PPI
            if (!linkSequence2PPI.contains(linkSequence)) {
                linkSequence2PPI[linkSequence].resize(experimentIntervalMeasurements.numIntervals());
                for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
                    int ppi = qMin(experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p1].numPacketsInFlight,
                                   experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p2].numPacketsInFlight);
                    linkSequence2PPI[linkSequence][i] = ppi;
                }
            } else {
                for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
                    int ppi = qMin(experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p1].numPacketsInFlight,
                                   experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p2].numPacketsInFlight);
                    linkSequence2PPI[linkSequence][i] = qMin(linkSequence2PPI[linkSequence][i], ppi);
                }
            }
            // linkSequence2IntervalMask
            if (!linkSequence2IntervalMask.contains(linkSequence)) {
                QList<qint32> links = linkSequence.toList();
                linkSequence2IntervalMask[linkSequence] = linkIntervalMask[links.first()];
                foreach (qint32 e, links) {
                    for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
                        if (USE_INTERVAL_MASK) {
                            linkSequence2IntervalMask[linkSequence][i] = linkSequence2IntervalMask[linkSequence][i] &&
                                                                         linkIntervalMask[e][i];
                        } else {
                            linkSequence2IntervalMask[linkSequence][i] = true;
                        }
                    }
                }
            }
        }
    }

    // Strategy:
    // foreach linkSeq
    //   foreach interval
    //     foreach iteration
    //       foreach path
    //         resample end-to-end data
    //         use threshold to decide if path is good
    //     foreach path
    //       pick the majority of decisions to decide if path is good
    //     foreach path pair (p1, p2) such that class[p1] == class[p2]:
    //       compute the estimated congestion probability of the link sequence and record it with the class
    foreach (QInt32Set linkSequence, linkSequence2PathPairs.uniqueKeys()) {
        const QVector<bool> &intervalMask = linkSequence2IntervalMask[linkSequence];
        const QVector<int> &intervalPPI = linkSequence2PPI[linkSequence];

        // index: interval
        // value: true if all data for the interval is valid
        QVector<bool> intervalValid;
        // first index: interval
        // second index: path
        // value: true if path is good, false if path is congested, undefined if intervalValid[interval] is false
        QVector<QVector<bool> > intervalPathState;

        intervalValid.fill(false, experimentIntervalMeasurements.numIntervals());
        intervalPathState.resize(experimentIntervalMeasurements.numIntervals());

        for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
            if (!intervalMask[i])
                continue;
            intervalValid[i] = true;
            // index: path
            // value: number of samples for which the path is detected as good
            QVector<int> pathGoodCount;
            pathGoodCount.fill(0, experimentIntervalMeasurements.numPaths);
            // index: path
            // value: number of samples for which the path is detected as congested
            QVector<int> pathCongestedCount;
            pathCongestedCount.fill(0, experimentIntervalMeasurements.numPaths);

            // foreach path, resample end-to-end data and use threshold to decide if path is good
            foreach (qint32 p, linkSequence2Paths[linkSequence]) {
                if (experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p].numPacketsInFlight < minNumPackets ||
                    intervalPPI[i] < minNumPackets) {
                    intervalValid[i] = false;
                    break;
                }
                for (int samplingIteration = 0; samplingIteration < numSamplingIterations; samplingIteration++) {
                    GraphIntervalMeasurements resampledMeasurements = experimentIntervalMeasurements.intervalMeasurements[i];
                    resampledMeasurements.pathMeasurements[p].sample(intervalPPI[i]);

                    bool ok;
                    qreal loss = 1.0 - resampledMeasurements.pathMeasurements[p].successRate(&ok);
                    if (!ok) {
                        intervalValid[i] = false;
                        break;
                    }

                    if (loss < lossThreshold) {
                        pathGoodCount[p]++;
                    } else {
                        pathCongestedCount[p]++;
                    }
                }
            }

            if (!intervalValid[i])
                continue;

            intervalPathState[i].resize(experimentIntervalMeasurements.numPaths);
            // foreach path, pick the majority to decide if path is good
            foreach (qint32 p, linkSequence2Paths[linkSequence]) {
                intervalPathState[i][p] = pathGoodCount[p] > pathCongestedCount[p];
            }
        }

        qDebug() << "sequence" << linkSequence << intervalValid.count(true) << "intervals";

        foreach (QInt32Pair pathPair, linkSequence2PathPairs[linkSequence]) {
            qint32 p1 = pathPair.first;
            qint32 p2 = pathPair.second;

            // compute prob. of non-congestion for path 1
            qreal probGood1 = 0;
            qreal probGood1Count = 0;
            for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
                if (intervalValid[i]) {
                    if (intervalPathState[i][p1]) {
                        probGood1 += 1;
                    }
                    probGood1Count += 1;
                }
            }
            probGood1 /= qMax(1.0, probGood1Count);

            // compute prob. of non-congestion for path 2
            qreal probGood2 = 0;
            qreal probGood2Count = 0;
            for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
                if (intervalValid[i]) {
                    if (intervalPathState[i][p2]) {
                        probGood2 += 1;
                    }
                    probGood2Count += 1;
                }
            }
            probGood2 /= qMax(1.0, probGood2Count);

            // compute prob. of non-congestion for paths 1 & 2 (interval is non-congested if both paths are non-congested)
            qreal probGood12 = 0;
            qreal probGood12Count = 0;
            for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
                if (intervalValid[i]) {
                    if (intervalPathState[i][p1] &&
                        intervalPathState[i][p2]) {
                        probGood12 += 1;
                    }
                    probGood12Count += 1;
                }
            }
            probGood12 /= qMax(1.0, probGood12Count);

            // this is the estimated probability of non-congestion for the link sequence
            qreal estimatedProbGoodSequence = qMin(1.0, qMax(0.0, probGood1 * probGood2 / qMax(1.602e-19, probGood12)));

            // compute the ground truth for comparison
            // note that we do not resample here... so there might be some extra difference because of this
            qreal trueProbGoodSequence = 0;
            qreal trueProbGoodCount = 0;
            QVector<bool> trueStateSequence;
            trueStateSequence.fill(true, experimentIntervalMeasurements.numIntervals());
            for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
                if (experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p1].numPacketsInFlight <= minNumPackets &&
                    experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p2].numPacketsInFlight <= minNumPackets) {
                    continue;
                }
                if (!intervalValid[i])
                    continue;
                bool congestedInterval = false;
                foreach (qint32 e, linkSequence) {
                    QInt32Pair ep1 = QInt32Pair(e, p1);
                    QInt32Pair ep2 = QInt32Pair(e, p2);
                    bool ok1;
                    qreal loss1 = 1.0 - experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep1].successRate(&ok1);
                    bool ok2;
                    qreal loss2 = 1.0 - experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep2].successRate(&ok2);
                    if (ok1 && ok2) {
                        if (loss1 >= lossThreshold &&
                            loss2 >= lossThreshold) {
                            congestedInterval = true;
                            break;
                        }
                    }
                }
                trueStateSequence[i] = !congestedInterval;
                if (!congestedInterval) {
                    trueProbGoodSequence += 1;
                }
                trueProbGoodCount += 1;
            }
            trueProbGoodSequence /= qMax(1.0, trueProbGoodCount);

            // save the result in the appropriate class group
            int ppi1 = 1;
            int ppi2 = 1;
            int class1 = pathTrafficClass[p1] + 1;
            int class2 = pathTrafficClass[p2] + 1;
            int bin1 = 1 + int(ppi1 / binSize);
            int bin2 = 1 + int(ppi2 / binSize);

            if (class1 == class2) {
                if (class1 == 1 && class2 == 1) {
                    linkSequence2pathPair11[linkSequence] = true;
                } else if (class1 == 2 && class2 == 2) {
                    linkSequence2pathPair22[linkSequence] = true;
                }

                if (bin1 == bin2) {
                    QString key = QString("b%1c%2").arg(bin1).arg(class1);
                    linkSequence2ClassBin2computedProbsCongestion[linkSequence][key] << 1.0 - estimatedProbGoodSequence;
                    linkSequence2ClassBin2trueProbsCongestion[linkSequence][key] << 1.0 - trueProbGoodSequence;
                    linkSequence2Bins[linkSequence].insert(QString("b%1").arg(bin1));
                    qDebug() << linkSequence << "->" << (p1 + 1) << (p2 + 1)
                             << "estimated" << 100 * (1.0 - estimatedProbGoodSequence)
                             << "true" << 100 * (1.0 - trueProbGoodSequence)
                                ;
                }
            }

            if (diagnostic) {
                // Diagnostic code
                if (linkSequence == (QList<qint32>() << 0 << 2).toSet() &&
                    ((p1 == 0 && p2 == 2) || (p1 == 4 && p2 == 6)) ) {
                    QFile file1(QString("p%1.txt").arg(p1 + 1));
                    QFile file2(QString("p%1.txt").arg(p2 + 1));
                    file1.open(QFile::WriteOnly | QFile::Truncate);
                    file2.open(QFile::WriteOnly | QFile::Truncate);

                    QTextStream out1(&file1);
                    QTextStream out2(&file2);
                    out1 << "Data for path " << (p1 + 1) << "\n";
                    out2 << "Data for path " << (p2 + 1) << "\n";
                    for (int i = firstTransientCut; i < experimentIntervalMeasurements.numIntervals() - lastTransientCut; i++) {
                        if (!intervalMask[i])
                            continue;
                        if (!intervalValid[i])
                            continue;
                        if (experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[0].numPacketsDropped > 0 ||
                            experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[2].numPacketsDropped > 0 ||
                            experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[4].numPacketsDropped > 0 ||
                            experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[6].numPacketsDropped > 0) {

                            out1 << "\n";
                            out2 << "\n";

                            out1 << "\n";
                            out2 << "\n";

                            out1 << "======================================================================\n";
                            out2 << "======================================================================\n";

                            out1 << "Interval " << (i + 1) << "\n";
                            out2 << "Interval " << (i + 1) << "\n";

                            out1 << "\n";
                            out2 << "\n";

                            out1 << "Real end-to-end data\n";
                            out2 << "Real end-to-end data\n";

                            out1 << experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p1].numPacketsDropped
                                 << " / "
                                 << experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p1].numPacketsInFlight
                                 << " => " << (100 * experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p1].successRate())
                                 << " %"
                                 << "\n";
                            out2 << experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p2].numPacketsDropped
                                 << " / "
                                 << experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p2].numPacketsInFlight
                                 << " => " << (100 * experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p2].successRate())
                                 << " %"
                                 << "\n";

                            int numLines1 = experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p1].events.toString().count('\n');
                            int numLines2 = experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p2].events.toString().count('\n');
                            int numLinesMax = qMax(qMax(experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[0].events.toString().count('\n'),
                                                   experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[2].events.toString().count('\n')),
                                    qMax(experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[4].events.toString().count('\n'),
                                    experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[6].events.toString().count('\n')));

                            out1 << experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p1].events.toString() << "\n";
                            out2 << experimentIntervalMeasurements.intervalMeasurements[i].pathMeasurements[p2].events.toString() << "\n";
                            for (; numLines1 < numLinesMax; numLines1++) {
                                out1 << "\n";
                            }
                            for (; numLines2 < numLinesMax; numLines2++) {
                                out2 << "\n";
                            }

                            out1 << "Sampled end-to-end data\n";
                            out2 << "Sampled end-to-end data\n";

                            out1 << QString("State: %1\n").arg(intervalPathState[i][p1] ? "good" : "congested");
                            out2 << QString("State: %1\n").arg(intervalPathState[i][p2] ? "good" : "congested");

                            out1 << "\n";
                            out2 << "\n";

                            out1 << "True sequence data\n";
                            out2 << "True sequence data\n";

                            out1 << QString("State: %1\n").arg(trueStateSequence[i] ? "good" : "congested");
                            out2 << QString("State: %1\n").arg(trueStateSequence[i] ? "good" : "congested");

                            out1 << "\n";
                            out2 << "\n";

                            foreach (qint32 e, linkSequence) {
                                out1 << QString("Drops on link %1:\n").arg(e + 1);
                                out2 << QString("Drops on link %1:\n").arg(e + 1);

                                QInt32Pair ep1 = QInt32Pair(e, p1);
                                QInt32Pair ep2 = QInt32Pair(e, p2);
                                QInt32Pair e0 = QInt32Pair(e, 0);
                                QInt32Pair e2 = QInt32Pair(e, 2);
                                QInt32Pair e4 = QInt32Pair(e, 4);
                                QInt32Pair e6 = QInt32Pair(e, 6);
                                out1 << experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep1].numPacketsDropped
                                     << " / "
                                     << experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep1].numPacketsInFlight
                                     << " => " << (100 * experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep1].successRate())
                                     << " %"
                                     << "\n";
                                out2 << experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep2].numPacketsDropped
                                     << " / "
                                     << experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep2].numPacketsInFlight
                                     << " => " << (100 * experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep2].successRate())
                                     << " %"
                                     << "\n";

                                int numLines1 = experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep1].events.toString().count('\n');
                                int numLines2 = experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep2].events.toString().count('\n');
                                int numLinesMax = qMax(qMax(experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[e0].events.toString().count('\n'),
                                                       experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[e2].events.toString().count('\n')),
                                        qMax(experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[e4].events.toString().count('\n'),
                                        experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[e6].events.toString().count('\n')));

                                out1 << experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep1].events.toString() << "\n";
                                out2 << experimentIntervalMeasurements.intervalMeasurements[i].perPathEdgeMeasurements[ep2].events.toString() << "\n";
                                for (; numLines1 < numLinesMax; numLines1++) {
                                    out1 << "\n";
                                }
                                for (; numLines2 < numLinesMax; numLines2++) {
                                    out2 << "\n";
                                }

                                out1 << "\n";
                                out2 << "\n";
                            }
                        }
                    }
                }
            }
        }
    }

    // Detection
    QHash<QSet<qint32>, QList<qreal> > linkSequence2NeutralClues;
    QHash<QSet<qint32>, QList<qreal> > linkSequence2NonNeutralClues;
    QHash<QSet<qint32>, QString > linkSequence2DetectedNeutrality;
    QHash<QSet<qint32>, QString > linkSequence2DetectionResult;
    if (0) {
        // Gap method
        foreach (QInt32Set linkSequence, linkSequence2neutrality.uniqueKeys()) {
            foreach (QString bin, linkSequence2Bins[linkSequence]) {
                QString bc1 = QString("%1c1").arg(bin);
                QString bc2 = QString("%1c2").arg(bin);
                if (!linkSequence2ClassBin2computedProbsCongestion[linkSequence].contains(bc1) ||
                    !linkSequence2ClassBin2computedProbsCongestion[linkSequence].contains(bc2))
                    continue;
                qreal d = fabs(distance(linkSequence2ClassBin2computedProbsCongestion[linkSequence][bc1],
                                        linkSequence2ClassBin2computedProbsCongestion[linkSequence][bc2]));
                qreal reference = qMax(0.01, qMax(median(linkSequence2ClassBin2computedProbsCongestion[linkSequence][bc1]),
                                                  median(linkSequence2ClassBin2computedProbsCongestion[linkSequence][bc2])));
                if (d < reference * gapThreshold) {
                    linkSequence2NeutralClues[linkSequence] << d / reference;
                } else {
                    linkSequence2NonNeutralClues[linkSequence] << d / reference;
                }
            }
            if (linkSequence2NeutralClues[linkSequence].isEmpty() && linkSequence2NonNeutralClues[linkSequence].isEmpty()) {
                linkSequence2DetectedNeutrality[linkSequence] = "undecidable";
                linkSequence2DetectionResult[linkSequence] = "undecidable";
            } else if (!linkSequence2NeutralClues[linkSequence].isEmpty() && linkSequence2NonNeutralClues[linkSequence].isEmpty()) {
                linkSequence2DetectedNeutrality[linkSequence] = "neutral (strong)";
                linkSequence2DetectionResult[linkSequence] = (linkSequence2neutrality[linkSequence] ? "true negative" : "false negative");
            } else if (linkSequence2NeutralClues[linkSequence].isEmpty() && !linkSequence2NonNeutralClues[linkSequence].isEmpty()) {
                linkSequence2DetectedNeutrality[linkSequence] = "non-neutral (strong)";
                linkSequence2DetectionResult[linkSequence] = (linkSequence2neutrality[linkSequence] ? "false positive" : "true positive");
            } else if (sum(linkSequence2NeutralClues[linkSequence]) > sum(linkSequence2NonNeutralClues[linkSequence])) {
                linkSequence2DetectedNeutrality[linkSequence] = "neutral (weak)";
                linkSequence2DetectionResult[linkSequence] = (linkSequence2neutrality[linkSequence] ? "true negative" : "false negative");
            } else {
                linkSequence2DetectedNeutrality[linkSequence] = "non-neutral (weak)";
                linkSequence2DetectionResult[linkSequence] = (linkSequence2neutrality[linkSequence] ? "false positive" : "true positive");
            }
        }
    } else {
        // Global clustering method
        QVector<QPair<QInt32Set, QString> > bins;
        QVector<qreal> gaps;
        foreach (QInt32Set linkSequence, linkSequence2neutrality.uniqueKeys()) {
            foreach (QString bin, linkSequence2Bins[linkSequence]) {
                QString bc1 = QString("%1c1").arg(bin);
                QString bc2 = QString("%1c2").arg(bin);
                if (!linkSequence2ClassBin2computedProbsCongestion[linkSequence].contains(bc1) ||
                    !linkSequence2ClassBin2computedProbsCongestion[linkSequence].contains(bc2))
                    continue;
                // Measure the distance in percent to ease debugging
                qreal d = 100.0 * fabs(distance(linkSequence2ClassBin2computedProbsCongestion[linkSequence][bc1],
                                                linkSequence2ClassBin2computedProbsCongestion[linkSequence][bc2]));
                bins.append(QPair<QInt32Set, QString>(linkSequence, bin));
                gaps.append(d);
            }
        }
        const int repeats = 7;
        // first index: iteration
        // second index: bin (or gap)
        // value: cluster (0 or 1)
        QVector<QVector<int> > repeatedGapCLusters;
        for (int iteration = 0; iteration < repeats; iteration++) {
            QVector<int> gapClusters = kMeans1D(gaps, 2);
            qDebug() << "Gaps:" << gaps;
            qDebug() << "Clusters:" << clusterPoints1D(gaps, gapClusters, 2);
            repeatedGapCLusters << gapClusters;
        }
        // Consensus
        QVector<int> finalClusters;
        finalClusters.resize(gaps.count());
        for (int i = 0; i < gaps.count(); i++) {
            finalClusters[i] = 0;
            for (int iteration = 0; iteration < repeats; iteration++) {
                finalClusters[i] += repeatedGapCLusters[iteration][i];
            }
            finalClusters[i] = (finalClusters[i] <= repeats / 2) ? 0 : 1;
        }
        qDebug() << "Gaps:" << gaps;
        qDebug() << "Final clusters:" << clusterPoints1D(gaps, finalClusters, 2);
        // Cluster 0 means non-neutral, cluster 1 means neutral. Assign the result to the sequences:
        foreach (QInt32Set linkSequence, linkSequence2neutrality.uniqueKeys()) {
            linkSequence2DetectedNeutrality[linkSequence] = "undecidable";
            linkSequence2DetectionResult[linkSequence] = "undecidable";
        }
        for (int binIndex = 0; binIndex < bins.count(); binIndex++) {
            QInt32Set linkSequence = bins[binIndex].first;
            if (finalClusters[binIndex] == 1) {
                linkSequence2DetectedNeutrality[linkSequence] = "non-neutral";
                linkSequence2DetectionResult[linkSequence] = (linkSequence2neutrality[linkSequence] ? "false positive" : "true positive");
                for (int iteration = 0; iteration < repeats; iteration++) {
                    if (repeatedGapCLusters[iteration][binIndex] == finalClusters[binIndex]) {
                        linkSequence2NonNeutralClues[linkSequence] << gaps[binIndex] / 100.0;
                    } else {
                        linkSequence2NeutralClues[linkSequence] << gaps[binIndex] / 100.0;
                    }
                }
            } else if (finalClusters[binIndex] == 0) {
                linkSequence2DetectedNeutrality[linkSequence] = "neutral";
                linkSequence2DetectionResult[linkSequence] = (linkSequence2neutrality[linkSequence] ? "true negative" : "false negative");
                for (int iteration = 0; iteration < repeats; iteration++) {
                    if (repeatedGapCLusters[iteration][binIndex] == finalClusters[binIndex]) {
                        linkSequence2NeutralClues[linkSequence] << gaps[binIndex] / 100.0;
                    } else {
                        linkSequence2NonNeutralClues[linkSequence] << gaps[binIndex] / 100.0;
                    }
                }
            } else {
                Q_ASSERT_FORCE(false);
            }
        }
    }

    // Metrics for the raw result
    int truePositives = 0;
    int falsePositives = 0;
    int totalNonNeutral = 0;
    int trueNegatives = 0;
    int falseNegatives = 0;
    int totalNeutral = 0;
    foreach (QInt32Set linkSequence, linkSequence2neutrality.uniqueKeys()) {
        if (!linkSequence2pathPair11[linkSequence] || !linkSequence2pathPair22[linkSequence])
            continue;
        if (linkSequence2DetectionResult[linkSequence] == "undecidable")
            continue;
        if (linkSequence2neutrality[linkSequence]) {
            totalNeutral++;
        } else {
            totalNonNeutral++;
        }
        if (linkSequence2DetectionResult[linkSequence] == "true positive") {
            truePositives++;
        } else if (linkSequence2DetectionResult[linkSequence] == "true negative") {
            trueNegatives++;
        } else if (linkSequence2DetectionResult[linkSequence] == "false negative") {
            falseNegatives++;
        } else if (linkSequence2DetectionResult[linkSequence] == "false positive") {
            falsePositives++;
        }
    }

    // Refined result
    QSet<QInt32Set> nonNeutralSequencesKept;
    QHash<QInt32Set, QString> nonNeutralSequences2KeepReason;
    foreach (QInt32Set linkSequence, linkSequence2neutrality.uniqueKeys()) {
        if (linkSequence2DetectedNeutrality[linkSequence] == "non-neutral") {
            QList<QInt32Set> neutralSubSequences;
            QList<QInt32Set> nonNeutralSubSequences;
            foreach (QInt32Set subSequence, linkSequence2neutrality.uniqueKeys()) {
                if (linkSequence.contains(subSequence) && linkSequence != subSequence) {
                    if (linkSequence2DetectedNeutrality[subSequence] == "neutral") {
                        neutralSubSequences << subSequence;
                    } else if (linkSequence2DetectedNeutrality[subSequence] == "non-neutral") {
                        nonNeutralSubSequences << subSequence;
                    }
                }
            }
            // Compute unions
            QInt32Set neutralUnion;
            foreach (QInt32Set subSequence, neutralSubSequences) {
                neutralUnion.unite(subSequence);
            }

            QInt32Set nonNeutralUnion;
            foreach (QInt32Set subSequence, nonNeutralSubSequences) {
                nonNeutralUnion.unite(subSequence);
            }
            // Compute overall union and intersection
            QInt32Set completeUnion = neutralUnion;
            completeUnion.unite(nonNeutralUnion);

            bool keep;
            if (completeUnion == linkSequence && !nonNeutralUnion.isEmpty()) {
                // discard, nothing to do
                keep = false;
            } else {
                nonNeutralSequencesKept.insert(linkSequence);
                keep = true;
            }

            // Log reason
            QString reason;
            reason += QString("Covered by non-neutral subsequences: ");
            foreach (QInt32Set subSequence, nonNeutralSubSequences) {
                reason += reason.endsWith(">") ? ", " : "";
                reason += "<";
                foreach (qint32 e, linkSequence2OrderedLinkSequence[subSequence]) {
                    reason += QString("%1%2").arg(reason.endsWith("<") ? "" : ", ").arg(e + 1);
                }
                reason += ">";
            }
            reason += "\n";

            reason += QString("Covered by neutral subsequences: ");
            foreach (QInt32Set subSequence, neutralSubSequences) {
                reason += reason.endsWith(">") ? ", " : "";
                reason += "<";
                foreach (qint32 e, linkSequence2OrderedLinkSequence[subSequence]) {
                    reason += QString("%1%2").arg(reason.endsWith("<") ? "" : ", ").arg(e + 1);
                }
                reason += ">";
            }
            reason += "\n";

            reason += QString("Union of non-neutral subsequences: ");
            reason += "{";
            foreach (qint32 e, nonNeutralUnion) {
                reason += QString("%1%2").arg(reason.endsWith("{") ? "" : ", ").arg(e + 1);
            }
            reason += "}";
            reason += "\n";

            reason += QString("Union of neutral subsequences: ");
            reason += "{";
            foreach (qint32 e, neutralUnion) {
                reason += QString("%1%2").arg(reason.endsWith("{") ? "" : ", ").arg(e + 1);
            }
            reason += "}";
            reason += "\n";

            reason += QString("Union of non-neutral and neutral subsequences: ");
            reason += "{";
            foreach (qint32 e, completeUnion) {
                reason += QString("%1%2").arg(reason.endsWith("{") ? "" : ", ").arg(e + 1);
            }
            reason += "}";
            reason += "\n";

            reason += QString("Union of non-neutral and neutral subsequences covers the sequence: %1\n")
                      .arg(completeUnion == linkSequence ? "yes" : "NO");

            reason += QString("There is at least one non-neutral subsequence: %1\n")
                      .arg(!nonNeutralUnion.isEmpty() ? "yes" : "NO");

            reason += QString("Decision: %1\n")
                      .arg(!keep ? "discard" : "KEEP");

            nonNeutralSequences2KeepReason[linkSequence] = reason;
        }
    }

    qreal granularity = 0;
    foreach (QInt32Set linkSequence, nonNeutralSequencesKept) {
        granularity += linkSequence.count();
    }
    granularity /= qMax(1, nonNeutralSequencesKept.count());

    QSet<qint32> actualNonNeutralLinks;
    foreach (NetGraphEdge edge, g.edges) {
        if (!edge.isNeutral()) {
            actualNonNeutralLinks.insert(edge.index);
        }
    }
    QSet<qint32> nonNeutralLinksDetected;
    foreach (QInt32Set linkSequence, nonNeutralSequencesKept) {
        foreach (qint32 e, linkSequence) {
            if (actualNonNeutralLinks.contains(e)) {
                nonNeutralLinksDetected.insert(e);
            }
        }
    }
    qreal coverage = nonNeutralLinksDetected.count() / qMax(1, actualNonNeutralLinks.count());

    // save result
    QString dataFile;
    dataFile += QString("Experiment\t%1\tinterval\t%2\n").arg(experimentSuffix).arg(experimentIntervalMeasurements.intervalSize / 1.0e9);
    dataFile += QString("Non-neutral links");
    foreach (NetGraphEdge edge, g.edges) {
        if (!edge.isNeutral()) {
            dataFile += QString("\t%1").arg(edge.index + 1);
        }
    }
    dataFile += "\n";
    dataFile += "\n";
    foreach (QInt32Set linkSequence, linkSequence2neutrality.uniqueKeys()) {
        if (!linkSequence2pathPair11[linkSequence] || !linkSequence2pathPair22[linkSequence])
            continue;

        dataFile += QString("Link sequence\t");
        dataFile += QString("neutrality\t%1\t").arg(linkSequence2neutrality[linkSequence] ? "neutral" : "non-neutral");
        dataFile += QString("links");
        foreach (qint32 e, linkSequence2OrderedLinkSequence[linkSequence]) {
            dataFile += QString("\t%1").arg(e + 1);
        }
        dataFile += "\n";

        foreach (QString classBin, sorted(linkSequence2ClassBin2computedProbsCongestion[linkSequence].uniqueKeys())) {
            dataFile += QString("Class\t%1").arg(classBin);
            foreach (qreal prob, linkSequence2ClassBin2computedProbsCongestion[linkSequence][classBin]) {
                dataFile += QString("\t%1").arg(prob * 100.0);
            }
            dataFile += "\n";
        }
        dataFile += "\n";

        foreach (QString classBin, sorted(linkSequence2ClassBin2trueProbsCongestion[linkSequence].uniqueKeys())) {
            dataFile += QString("True class\t%1").arg(classBin);
            foreach (qreal prob, linkSequence2ClassBin2trueProbsCongestion[linkSequence][classBin]) {
                dataFile += QString("\t%1").arg(prob * 100.0);
            }
            dataFile += "\n";
        }
        dataFile += "\n";

        dataFile += QString("Neutral clues");
        foreach (qreal c, linkSequence2NeutralClues[linkSequence]) {
            dataFile += QString("\t%1").arg(c * 100.0);
        }
        dataFile += "\n";

        dataFile += QString("Non-neutral clues");
        foreach (qreal c, linkSequence2NonNeutralClues[linkSequence]) {
            dataFile += QString("\t%1").arg(c * 100.0);
        }
        dataFile += "\n";

        dataFile += QString("Detection\t%1\n").arg(linkSequence2DetectedNeutrality[linkSequence]);
        dataFile += QString("Result\t%1\n").arg(linkSequence2DetectionResult[linkSequence]);

        dataFile += "\n";
    }
    QString dataName = workingDir + "/" +
                       QString("seq-analysis-%1-%2-bins-%3-lossth-%4-samplings-%5-gapth-%6")
                       .arg(experimentSuffix)
                       .arg(timeToString(experimentIntervalMeasurements.intervalSize))
                       .arg(binSize, 0, 'f')
                       .arg(lossThreshold, 0, 'f', 2)
                       .arg(numSamplingIterations)
                       .arg(gapThreshold) + ".txt";
    if (!saveFile(dataName, dataFile))
        return false;

    // save html report
    QString nonNeutralLinksStr;
    for (qint32 e = 0; e < g.edges.count(); e++) {
        if (!g.edges[e].isNeutral()) {
            nonNeutralLinksStr += QString(nonNeutralLinksStr.isEmpty() ? "" : ", ") + QString("%1").arg(e + 1);
        }
    }

    QHash<int, QSet<QString> > class2traffic;
    foreach (NetGraphConnection c, g.connections) {
        class2traffic[c.trafficClass].insert(c.encodedType);
    }
    QString htmlTraffic;
    foreach (int c, sorted(class2traffic.uniqueKeys())) {
        htmlTraffic += QString("      <li>Traffic for class %1:").arg(c + 1);
        foreach (QString traffic, class2traffic[c]) {
            htmlTraffic += QString("%1%2")
                           .arg(htmlTraffic.endsWith(":") ? "" : ", ")
                           .arg(traffic);
        }
        htmlTraffic += QString("</li>\n");
    }

    QString html;
    html = QString("<!DOCTYPE html>\n"
                   "<html>\n"
                   "<head>\n"
                   "  <meta charset=\"UTF-8\">\n"
                   "  <title>Neutrality Project Plan</title>\n"
				   "  <link rel=\"shortcut icon\" type=\"image/png\" href=\"../../../html/plan.png\">\n"
				   "  <link rel=\"stylesheet\" href=\"../../../html/style.css\">\n"
                   "</head>\n"
                   "<body>\n"
                   "<div class=\"section\">\n"
                   "  <h2>Experiment: %1</h2>\n"
				   "  <img src=\"../../../html/pegasus.png\"></img>\n"
                   "  <p>Experiment parameters:\n"
                   "    <ul>\n"
                   "      <li>Non-neutral links: %2</li>\n"
                   "%3"
                   "      <li>Interval size: %4</li>\n"
                   "      <li>Bin size: %5 packets per interval (irrelevant!)</li>\n"
                   "      <li>Loss threshold: %6 %</li>\n"
                   "      <li>Number of resamplings: %7</li>\n"
                   "      <li>Gap threshold: %8 %</li>\n"
                   "    </ul>\n"
                   "  </p>\n"
                   "  <div class=\"section\">\n"
                   "    <h3>Computed link sequence congestion probabilities:</h3>\n")
           .arg(experimentSuffix)
           .arg(nonNeutralLinksStr)
           .arg(htmlTraffic)
           .arg(timeToString(experimentIntervalMeasurements.intervalSize))
           .arg(binSize, 0, 'f')
           .arg(lossThreshold * 100.0)
           .arg(numSamplingIterations)
           .arg(gapThreshold * 100.0);

    html += QString("    <img src=\"%1/class-path-cong-probs-links.png\"></img>\n")
            .arg(QString("link-analysis-%1").arg(lossThreshold, 0, 'f', 2));
    html += QString("    <img src=\"%1/link-seq-cong-prob-all.png\"></img>\n")
            .arg(QString("seq-analysis-%1-%2-bins-%3-lossth-%4-samplings-%5-gapth-%6")
                 .arg(experimentSuffix)
                 .arg(timeToString(experimentIntervalMeasurements.intervalSize))
                 .arg(binSize, 0, 'f')
                 .arg(lossThreshold, 0, 'f', 2)
                 .arg(numSamplingIterations)
                 .arg(gapThreshold));
    html += QString("    <table>\n"
                    "    <tbody>\n"
                    "      <tr>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">#</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Link sequence</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Type</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Result</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Kept</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Prob. cong. for class 1 (%, estimated)</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Prob. cong. for class 1 (%, real)</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Prob. cong. for class 2 (%, estimated)</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Prob. cong. for class 2 (%, real)</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Gaps indicating neutrality</th>\n"
                    "        <th colspan=\"1\" class=\"vcenter\">Gaps indicating non-neutrality</th>\n"
                    "      </tr>\n");

    int rowIndex = 0;
    foreach (QInt32Set linkSequence, linkSequence2neutrality.uniqueKeys()) {
        if (!linkSequence2pathPair11[linkSequence] || !linkSequence2pathPair22[linkSequence])
            continue;

        if (linkSequence2DetectionResult[linkSequence].contains("undecidable"))
            continue;

        html += QString("      <tr>\n");

        // #
        html += QString("      <td>");
        html += QString("%1 ").arg(rowIndex + 1);
        rowIndex++;
        html += QString("      </td>\n");

        // seq
        html += QString("      <td>");
        foreach (qint32 e, linkSequence2OrderedLinkSequence[linkSequence]) {
            html += QString("%1 ").arg(e + 1);
        }
        html += QString("      </td>\n");

        // type
        html += QString("      <td nowrap>");
        html += (linkSequence2neutrality[linkSequence] ? "neutral" : "non-neutral");
        html += QString("      </td>\n");

        // result
        html += QString("      <td nowrap style=\"background-color:%1\">")
                .arg(linkSequence2DetectionResult[linkSequence].contains("false") ?
                         "#f99" :
                         linkSequence2DetectionResult[linkSequence].contains("positive") ?
                             "#9f9" :
                             linkSequence2DetectionResult[linkSequence].contains("undecidable") ?
                                 "#ff9" :
                                 "#fff");
        html += linkSequence2DetectionResult[linkSequence];
        html += QString("      </td>\n");

        // kept
        html += QString("      <td nowrap>%1</td>\n")
                .arg(linkSequence2DetectedNeutrality[linkSequence] == "neutral" ?
                         "kept" : nonNeutralSequencesKept.contains(linkSequence) ?
                             "KEPT" : "discarded");

        // class 1 estimated
        html += QString("      <td>");
        foreach (QString classBin, sorted(linkSequence2ClassBin2computedProbsCongestion[linkSequence].uniqueKeys())) {
            if (classBin.endsWith("1")) {
                html += QString("%1:").arg(classBin);
                foreach (qreal prob, linkSequence2ClassBin2computedProbsCongestion[linkSequence][classBin]) {
                    html += QString("%1%2").arg(html.endsWith(":") ? " " : ", ").arg(prob * 100.0);
                }
                html += "<br/>";
            }
        }
        html += QString("      </td>\n");

        // class 1 real
        html += QString("      <td>");
        foreach (QString classBin, sorted(linkSequence2ClassBin2trueProbsCongestion[linkSequence].uniqueKeys())) {
            if (classBin.endsWith("1")) {
                html += QString("%1:").arg(classBin);
                foreach (qreal prob, linkSequence2ClassBin2trueProbsCongestion[linkSequence][classBin]) {
                    html += QString("%1%2").arg(html.endsWith(":") ? " " : ", ").arg(prob * 100.0);
                }
                html += "<br/>";
            }
        }
        html += QString("      </td>\n");

        // class 2 estimated
        html += QString("  <td>");
        foreach (QString classBin, sorted(linkSequence2ClassBin2computedProbsCongestion[linkSequence].uniqueKeys())) {
            if (classBin.endsWith("2")) {
                html += QString("%1:").arg(classBin);
                foreach (qreal prob, linkSequence2ClassBin2computedProbsCongestion[linkSequence][classBin]) {
                    html += QString("%1%2").arg(html.endsWith(":") ? " " : ", ").arg(prob * 100.0);
                }
                html += "<br/>";
            }
        }
        html += QString("      </td>\n");

        // class 2 real
        html += QString("      <td>");
        foreach (QString classBin, sorted(linkSequence2ClassBin2trueProbsCongestion[linkSequence].uniqueKeys())) {
            if (classBin.endsWith("2")) {
                html += QString("%1:").arg(classBin);
                foreach (qreal prob, linkSequence2ClassBin2trueProbsCongestion[linkSequence][classBin]) {
                    html += QString("%1%2").arg(html.endsWith(":") ? " " : ", ").arg(prob * 100.0);
                }
                html += "<br/>";
            }
        }
        html += QString("      </td>\n");

        // neutral clues
        html += QString("      <td>");
        foreach (qreal c, linkSequence2NeutralClues[linkSequence]) {
            html += QString("%1%2").arg(html.endsWith(">") ? "" : ", ").arg(c * 100.0);
        }
        html += QString("      </td>\n");

        // non-neutral clues
        html += QString("      <td>");
        foreach (qreal c, linkSequence2NonNeutralClues[linkSequence]) {
            html += QString("%1%2").arg(html.endsWith(">") ? "" : ", ").arg(c * 100.0);
        }
        html += QString("      </td>\n");

        html += QString("      </tr>\n");
    }
    html += QString("    </tbody>\n"
                    "    </table>\n");

    html += QString("    <p>True positives: %1 / %2 = %3 %</p>\n")
            .arg(truePositives)
            .arg(totalNonNeutral)
            .arg(truePositives * 100.0 / qMax(totalNonNeutral, 1));

    html += QString("    <p>True negatives: %1 / %2 = %3 %</p>\n")
            .arg(trueNegatives)
            .arg(totalNeutral)
            .arg(trueNegatives * 100.0 / qMax(totalNeutral, 1));

    html += QString("    <p>False positives: %1 / %2 = %3 %</p>\n")
            .arg(falsePositives)
            .arg(totalNeutral)
            .arg(falsePositives * 100.0 / qMax(totalNeutral, 1));

    html += QString("    <p>False negatives: %1 / %2 = %3 %</p>\n")
            .arg(falseNegatives)
            .arg(totalNonNeutral)
            .arg(falseNegatives * 100.0 / qMax(totalNonNeutral, 1));

    html += QString("    <p>Coverage: ");
    html += QString("%1 correctly detected as non-neutral (").arg(nonNeutralLinksDetected.count());
    foreach (qint32 e, sorted(nonNeutralLinksDetected.toList())) {
        html += QString("%1%2").arg(html.endsWith("(") ? "" : ", ").arg(e + 1);
    }
    html += QString(") / %1 actually non-neutral (").arg(actualNonNeutralLinks.count());
    foreach (qint32 e, sorted(actualNonNeutralLinks.toList())) {
        html += QString("%1%2").arg(html.endsWith("(") ? "" : ", ").arg(e + 1);
    }
    html += QString(") = %1 %").arg(coverage * 100.0);
    html += QString("</p>\n");

    html += QString("    <p>Granularity: %1</p>\n")
            .arg(granularity);

    html += QString("<p>Link sequence trimming</p>");
    foreach (QInt32Set linkSequence, linkSequence2neutrality.uniqueKeys()) {
        html += QString("      <ul>");
        if (linkSequence2DetectedNeutrality[linkSequence] == "non-neutral") {
            html += QString("        <li>&lt;");
            foreach (qint32 e, linkSequence2OrderedLinkSequence[linkSequence]) {
                html += QString("%1%2").arg(html.endsWith(";") ? "" : ", ").arg(e + 1);
            }
            html += QString("&gt; decision: %1<br/>\n").arg(nonNeutralSequencesKept.contains(linkSequence) ? "KEEP" : "discard");
            html += QString("        Reason:<br/>\n");
            html += QString(nonNeutralSequences2KeepReason[linkSequence])
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br/>");
            html += QString("        </li>\n");
        }
        html += QString("      </ul>\n");
    }

    html += QString("  </div>\n"
                    "</div>\n"
					"<script src=\"../../../html/todo.js\"></script>\n"
					"<script src=\"../../../html/toc.js\"></script>\n"
                    "</body>\n"
                    "</html>\n");

    QString htmlName = workingDir + "/" +
                       QString("seq-analysis-%1-%2-bins-%3-lossth-%4-samplings-%5-gapth-%6")
                       .arg(experimentSuffix)
                       .arg(timeToString(experimentIntervalMeasurements.intervalSize))
                       .arg(binSize, 0, 'f')
                       .arg(lossThreshold, 0, 'f', 2)
                       .arg(numSamplingIterations)
                       .arg(gapThreshold) + ".html";
    if (!saveFile(htmlName, html))
        return false;

    QDir::setCurrent(workingDir);
	QProcess::execute("../../../plotting-scripts-new/plot-edge-seq-cong-prob.py",
                      QStringList()
                      << "--in"
                      << QString("seq-analysis-%1-%2-bins-%3-lossth-%4-samplings-%5-gapth-%6")
                      .arg(experimentSuffix)
                      .arg(timeToString(experimentIntervalMeasurements.intervalSize))
                      .arg(binSize, 0, 'f')
                      .arg(lossThreshold, 0, 'f', 2)
                      .arg(numSamplingIterations)
                      .arg(gapThreshold) + ".txt"
                      << "--out"
                      << QString("seq-analysis-%1-%2-bins-%3-lossth-%4-samplings-%5-gapth-%6")
                      .arg(experimentSuffix)
                      .arg(timeToString(experimentIntervalMeasurements.intervalSize))
                      .arg(binSize, 0, 'f')
                      .arg(lossThreshold, 0, 'f', 2)
                      .arg(numSamplingIterations)
                      .arg(gapThreshold));
	QProcess::execute("../../../plotting-scripts-new/inline-html-images.py", QStringList() << htmlName);

    return true;
}

bool processResults(QString workingDir, QString graphName, QString experimentSuffix,
                    quint64 resamplePeriod, qreal binSize,
                    qreal lossThreshold,
                    int numResamplings,
                    qreal gapThreshold,
                    bool perFlowAnalysis)
{
    NetGraph g;
    if (!loadGraph(workingDir, graphName, g))
        return false;

	saveFile(workingDir + "/" + "graph.txt", g.toText());
    saveFile(workingDir + "/" + "experiment-suffix.txt", experimentSuffix);
    computePathCongestionProbabilities(workingDir, graphName, experimentSuffix, resamplePeriod);
    dumpPathIntervalData(workingDir, graphName, experimentSuffix, resamplePeriod);
    nonNeutralityAnalysis(workingDir, graphName, experimentSuffix,
                          resamplePeriod, binSize,
                          lossThreshold,
                          perFlowAnalysis);
    nonNeutralityDetection(workingDir, graphName, experimentSuffix,
                           resamplePeriod, binSize,
                           lossThreshold, numResamplings, gapThreshold,
                           perFlowAnalysis);

	return true;
}

bool processResults(QStringList params)
{
    if (params.isEmpty()) {
        qDebug() << "Missing argument for processResults";
        return false;
    }
    QString fileName = params.takeFirst();
    quint64 resamplePeriod = 0;
    qreal binSize = 1.0e9;
    bool perFlowAnalysis = false;
    qreal lossThreshold = 1.0 / 100.0;
    int numResamplings = 1;
    qreal gapThreshold = 50.0 / 100.0;
    while (!params.isEmpty()) {
        if (params.first() == "resample") {
            params.removeFirst();
            if (!params.isEmpty()) {
                bool ok;
                resamplePeriod = timeFromString(params.first(), &ok);
                if (!ok) {
                    qDebug() << "Bad argument for resample:" << params;
                    return false;
                }
                params.removeFirst();
                continue;
            } else {
                qDebug() << "Missing argument for resample:" << params;
                return false;
            }
        } else if (params.first() == "bin") {
            params.removeFirst();
            if (!params.isEmpty()) {
                bool ok;
                binSize = params.first().toDouble(&ok);
                if (!ok) {
                    qDebug() << "Bad argument for bin:" << params;
                    return false;
                }
                params.removeFirst();
                continue;
            } else {
                qDebug() << "Missing argument for bin:" << params;
                return false;
            }
        } else if (params.first() == "flows") {
            params.removeFirst();
            perFlowAnalysis = true;
            continue;
        } else if (params.first() == "paths") {
            params.removeFirst();
            perFlowAnalysis = false;
            continue;
        } else if (params.first() == "lossThreshold") {
            params.removeFirst();
            if (!params.isEmpty()) {
                bool ok;
                lossThreshold = params.first().toDouble(&ok);
                if (!ok || lossThreshold < 0 || lossThreshold > 1) {
                    qDebug() << "Bad argument for lossThreshold:" << params;
                    return false;
                }
                params.removeFirst();
                continue;
            } else {
                qDebug() << "Missing argument for bin:" << params;
                return false;
            }
        } else if (params.first() == "numResamplings") {
            params.removeFirst();
            if (!params.isEmpty()) {
                bool ok;
                numResamplings = params.first().toInt(&ok);
                if (!ok || numResamplings < 0) {
                    qDebug() << "Bad argument for numResamplings:" << params;
                    return false;
                }
                params.removeFirst();
                continue;
            } else {
                qDebug() << "Missing argument for bin:" << params;
                return false;
            }
        } else if (params.first() == "gapThreshold") {
            params.removeFirst();
            if (!params.isEmpty()) {
                bool ok;
                gapThreshold = params.first().toDouble(&ok);
                if (!ok || gapThreshold < 0) {
                    qDebug() << "Bad argument for gapThreshold:" << params;
                    return false;
                }
                params.removeFirst();
                continue;
            } else {
                qDebug() << "Missing argument for bin:" << params;
                return false;
            }
        }
        qDebug() << "Bad argument for --process-results:" << params;
        return false;
    }
    return processResults(fileName, resamplePeriod, binSize, lossThreshold, numResamplings, gapThreshold, perFlowAnalysis);
}
