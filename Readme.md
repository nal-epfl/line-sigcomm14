This is a snapshot of the repository https://github.com/nal-epfl/line as it was used in the experiments from our publication Network Neutrality Inference from SIGCOMM 2014.

An archive with experiment data that reproduces the results is available here: https://github.com/nal-epfl/line-sigcomm14/blob/master/data/sigcomm-experiments-repro-figure-data.tar.xz

## Instructions for reproducing the results from the SIGCOMM article.

You must follow these steps, which are described in the sections below:

* Download the code
* Prepare your hardware setup for the emulations
* Install the emulation software
* Run emulations using the network topologies and configurations used in the article
* Process the results and generate the plots

## Obtaining the code  

Checkout the repository containing the setup used in our article:

```
git clone https://github.com/nal-epfl/line-sigcomm14.git
```

## Preparing the hardware setup  

The setup uses 3 machines:

* A machine used to configure the experiments and process the data (Control center)
* A machine used for traffic generation (Traffic generator)
* A machine used for emulating the network (Network emulator)

The control center computer must satisfy a single requirement: it must run Ubuntu 12.04 LTS 64-bits.

The hardware requirements for the traffic generator and the network emulator are described in section Architecture of [doc/line.html](doc/line.html).

## Installing the software

Please follow the instructions from section System configuration of [doc/line.html](doc/line.html).

Additionally, to generate the plots on the control center you must install the matplotlib library:

```
apt-get install matplotlib
```

## Running the experiments  
In general, to run an emulation the following steps must be followed:

* Start the line-gui application on the control center machine
* Open a network topology or create a new one
* Configure link properties (rate, delay, policing/shaping)
* Configure the type of traffic that will be created by the traffic generator (e.g. how many TCP flows and between which hosts, transfer sizes, when flows are started etc.)
* Configure measurement parameters: sampling period, experiment duration
* Start the experiment

For the article, we used 23 experiments. Configuring them by hand in the GUI is possible but time-consuming and error-prone. To simplify the process, we added to the interface a set of buttons that automate the process, simulating the actions of the user to generate exactly the configurations used in the paper. They can be seen in this [screenshot](https://wiki.epfl.ch/line/documents/config-buttons.png). The parameter values set by the buttons are described in detail for each figure below. Additionally, you can also find the complete configuration of the topology and the traffic used in each experiment in a file named graph.txt placed in the experiment directory (the traffic generator syntax is documented in line-traffic/config-file-howto.txt in the repository); other parameters passed to the emulator are saved in a file named run-params.txt. You can find these files in the archive we provide with our experimental data.

### Figure 7a  
For generating this figure we run 4 experiments using the "quad" topology.

The shared link is neutral. To make things difficult for our algorithm, we try to create network conditions that could be misinterpreted as non-neutrality.

Traffic class 1 and class 2 have the same properties (such as RTT, TCP congestion control algorithm) except the flow transfer size: the flow transfer size of paths 1 and 2 is 1Mb, while that of paths 3 and 4 varies: 1Mb, 10Mb, 40Mb and 10Gb.

The four experiments used for the figure can be configured using the button "Sigcomm 7a" from the "Custom controls" window. The function that generates the configuration is:

```
line-gui/customcontrols_qos.cpp: void CustomControls::on_btnSigcomm7a_clicked()
```

After clicking the button, there should be four experiments in the queue. Click main window > "Queue" > "Start all" to start the emulations.

Here is a summary of the parameters set by the configuration code:

* Topology: quad
* Potential bottleneck links: link 1
* Bottleneck rate: 100 Mb/s
* Non-neutral links: none
* Rate limiting: none (all neutral links have a single drop-tail queue)
* Rate limit, class 1: N/A
* Rate limit, class 2: N/A
* Emulation duration: 600 s
* Sampling period: 50 ms
* Measured traffic, class 1: 70 x 1Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Measured traffic, class 2:
  * Experiment 1: 70 x 1Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 2: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 3: 20 x 40Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 4: 15 x 9999Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Background traffic, class 1: none
* Background traffic, class 2: none
* TCP congestion control: CUBIC
* Path RTT: 48 ms

### Figure 7b  
For generating this figure we run 4 experiments using the "quad" topology.

The shared link is neutral. To make things difficult for our algorithm, we try to create network conditions that could be misinterpreted as non-neutrality.

Traffic class 1 and class 2 have the same properties (such as transfer size, TCP congestion control algorithm) except RTT: the RTT of paths 1 and 2 is 50ms, while that of paths 3 and 4 varies from 50ms to 200ms.

The four experiments used for the figure can be configured using the button "Sigcomm 7b" from the "Custom controls" window. The function that generates the configuration is:

```
line-gui/customcontrols_qos.cpp: void CustomControls::on_btnSigcomm7b_clicked()
```

After clicking the button, there should be four experiments in the queue. Click main window > "Queue" > "Start all" to start the emulations.

Here is a summary of the parameters set by the configuration code:

* Topology: quad
* Potential bottleneck links: link 1
* Bottleneck rate: 100 Mb/s
* Non-neutral links: none
* Rate limiting: none (all neutral links have a single drop-tail queue)
* Rate limit, class 1: N/A
* Rate limit, class 2: N/A
* Emulation duration: 600 s
* Sampling period: 50 ms
* Measured traffic, class 1: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Measured traffic, class 2: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Background traffic, class 1: none
* Background traffic, class 2: none
* TCP congestion control: CUBIC
* Path RTT, class 1: 48 ms
* Path RTT, class 2:
  * Experiment 1: 48 ms
  * Experiment 2: 80 ms
  * Experiment 3: 120 ms
  * Experiment 4: 200 ms
  
### Figure 7c  
For generating this figure we run 2 experiments using the "quad" topology.

The shared link is neutral. To make things difficult for our algorithm, we try to create network conditions that could be misinterpreted as non-neutrality.

Traffic class 1 and class 2 have the same properties (such as RTT, transfer size) except the TCP congestion control algorithms: in one experiment all paths use TCP CUBIC, while in the other paths 1 and 2 use CUBIC and paths 3 and 4 use NewReno.

The two experiments used for the figure can be configured using the button "Sigcomm 7c" from the "Custom controls" window. The function that generates the configuration is:

```
line-gui/customcontrols_qos.cpp: void CustomControls::on_btnSigcomm7c_clicked()
```

After clicking the button, there should be two experiments in the queue. Click main window > "Queue" > "Start all" to start the emulations.

Here is a summary of the parameters set by the configuration code:

* Topology: quad
* Potential bottleneck links: link 1
* Bottleneck rate: 100 Mb/s
* Non-neutral links: none
* Rate limiting: none (all neutral links have a single drop-tail queue)
* Rate limit, class 1: N/A
* Rate limit, class 2: N/A
* Emulation duration: 600 s
* Sampling period: 50 ms
* Measured traffic, class 1: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Measured traffic, class 2: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Background traffic, class 1: none
* Background traffic, class 2: none
* TCP congestion control, class 1: CUBIC
* TCP congestion control, class 2:
  * Experiment 1: CUBIC
  * Experiment 2: NewReno
* Path RTT: 48 ms

### Figure 7d  
For generating this figure we run 4 experiments using the "quad" topology.

The shared link is non-neutral, policing the traffic in class 2. Here, the difficult scenarios for our algorithm are the ones where all the paths carry the same kind of traffic. In this plot we vary the transfer size for both traffic classes between 1, 10, 40 and 10000 Mb.

The four experiments used for the figure can be configured using the button "Sigcomm 7d" from the "Custom controls" window. The function that generates the configuration is:

```
line-gui/customcontrols_qos.cpp: void CustomControls::on_btnSigcomm7d_clicked()
```

After clicking the button, there should be four experiments in the queue. Click main window > "Queue" > "Start all" to start the emulations.

Here is a summary of the parameters set by the configuration code:

* Topology: quad
* Potential bottleneck links: link 1
* Bottleneck rate: 100 Mb/s
* Non-neutral links: link 1
* Rate limiting: policing (neutral links have a single drop-tail queue; non-neutral links use policing with 2 traffic classes)
* Rate limit, class 1: 100% of link rate (i.e. no limiting)
* Rate limit, class 2: 30% of link rate
* Emulation duration: 600 s
* Sampling period: 50 ms
* Measured traffic, class 1:
  * Experiment 1: 70 x 1Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 2: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 3: 20 x 40Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 4: 15 x 9999Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Measured traffic, class 2:
  * Experiment 1: 70 x 1Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 2: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 3: 20 x 40Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
  * Experiment 4: 15 x 9999Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Background traffic, class 1: none
* Background traffic, class 2: none
* TCP congestion control: CUBIC
* Path RTT: 48 ms

### Figure 7e  
For generating this figure we run 4 experiments using the "quad" topology.

The shared link is non-neutral, policing the traffic in class 2. Here, the difficult scenarios for our algorithm are the ones where all the paths carry the same kind of traffic. In this plot we vary the RTT for both traffic classes, between 50, 80, 120 and 200 ms.

The four experiments used for the figure can be configured using the button "Sigcomm 7e" from the "Custom controls" window. The function that generates the configuration is:

```
line-gui/customcontrols_qos.cpp: void CustomControls::on_btnSigcomm7e_clicked()
```

After clicking the button, there should be four experiments in the queue. Click main window > "Queue" > "Start all" to start the emulations.

Here is a summary of the parameters set by the configuration code:

* Topology: quad
* Potential bottleneck links: link 1
* Bottleneck rate: 100 Mb/s
* Non-neutral links: link 1
* Rate limiting: policing (neutral links have a single drop-tail queue; non-neutral links use policing with 2 traffic classes)
* Rate limit, class 1: 100% of link rate (i.e. no limiting)
* Rate limit, class 2: 30% of link rate
* Emulation duration: 600 s
* Sampling period: 50 ms
* Measured traffic, class 1: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Measured traffic, class 2: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Background traffic, class 1: none
* Background traffic, class 2: none
* TCP congestion control: CUBIC
* Path RTT:
  * Experiment 1: 48 ms
  * Experiment 2: 80 ms
  * Experiment 3: 120 ms
  * Experiment 4: 200 ms

### Figure 7f  
For generating this figure we run 4 experiments using the "quad" topology.

The shared link is non-neutral, policing the traffic in class 2. Here, the difficult scenarios for our algorithm are the ones where all the paths carry the same kind of traffic. In this plot we vary the policing weights of the shared link, between (1.0,0.2), (1.0,0.3), (1.0,0.4) and (1.0,0.5). The first number represents the fraction of the link rate allocated to class 1, the second number represents the fraction of the link rate allocated to class 2.

The four experiments used for the figure can be configured using the button "Sigcomm 7f" from the "Custom controls" window. The function that generates the configuration is:

```
line-gui/customcontrols_qos.cpp: void CustomControls::on_btnSigcomm7f_clicked()
```

After clicking the button, there should be four experiments in the queue. Click main window > "Queue" > "Start all" to start the emulations.

Here is a summary of the parameters set by the configuration code:

* Topology: quad
* Potential bottleneck links: link 1
* Bottleneck rate: 100 Mb/s
* Non-neutral links: link 1
* Rate limiting: policing (neutral links have a single drop-tail queue; non-neutral links use policing with 2 traffic classes)
* Rate limit, class 1: 100% of link rate (i.e. no limiting)
* Rate limit, class 2:
  * Experiment 1: 20% of link rate
  * Experiment 2: 30% of link rate
  * Experiment 3: 40% of link rate
  * Experiment 4: 50% of link rate
* Emulation duration: 600 s
* Sampling period: 50 ms
* Measured traffic, class 1: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Measured traffic, class 2: 15 x 10Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Background traffic, class 1: none
* Background traffic, class 2: none
* TCP congestion control: CUBIC
* Path RTT: 48 ms

### Figures 8a and 8b  
For generating this figure we run an experiment using the "pegasus" topology. This is a large topology with 4 types of traffic (first number = transfer size, second number = number of parallel flows):

* class 1 measured: 1Mb x 1 + 10Mb x 1 + 40Mb x 1
* class 2 measured: 10000Mb x 1
* class 1 background: 1Mb x 4 + 10Mb x 2 + 40Mb x 1 + 10000Mb x 1
* class 2 background: 10000Mb x 1

There are 3 non-neutral links, policing the traffic in class 2. There are two difficulties in this scenario: (1) that there is a large number of shared links and bottlenecks, but only a few of them are non-neutral; and (2) that measurements are taken for only some of the traffic (i.e. not every end-host in the network is a vantage point taking performance measurements).

The experiment used for the figure can be configured using the button "Sigcomm 8a/b" from the "Custom controls" window. The function that generates the configuration is:

```
line-gui/customcontrols_qos.cpp: void CustomControls::on_btnSigcomm8ab_clicked()
```

After clicking the button, there should be two experiments in the queue. Click main window > "Queue" > "Start all" to start the emulations.

Here is a summary of the parameters set by the configuration code:

* Topology: pegasus
* Potential bottleneck links: links 1-22
* Bottleneck rate: 100 Mb/s
* Non-neutral links: links 5, 14 and 20
* Rate limiting: policing (neutral links have a single drop-tail queue; non-neutral links use policing with 2 traffic classes)
* Rate limit, class 1: 100% of link rate (i.e. no limiting)
* Rate limit, class 2: 30% of link rate
* Emulation duration: 600 s
* Sampling period: 100 ms
* Measured traffic, class 1: 1 x 1Mb + 1 x 10Mb + 1 x 40Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Measured traffic, class 2: 1 x 9999Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Background traffic, class 1: 1 x 1Mb + 1 x 10Mb + 1 x 40Mb + 1 x 9999Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* Background traffic, class 2: 1 x 9999Mb (Pareto scale = 2, Poisson rate = 0.1 flows/s, sequential)
* TCP congestion control: CUBIC
* Path RTT: between 80 and 120 ms, depending on path length

## Processing the results and generating the plots  

### Figure 7a  
After running the experiments, open a terminal in a directory used to store the plot (e.g. repro-plots/7a). Copy the code from the text box in the "Custom controls" window to copy there the data from the emulations, then clear the text box in the "Custom controls" window.

To generate the plot, run:

```
../../plotting-scripts/plot-data.py --plot vary-transfer-size
```

The script simply reads the file path-congestion-probs.txt from each experiment, selects the line corresponding to the desired loss threshold (0.001, i.e. the first column in the file) and plots the path congestion probabilities (columns 2-5 in the file).

The plot is found in:

```
image-plot-7a-*/2. stats prob-cong-path - transferSize.png
```

### Figure 7b  
After running the experiments, open a terminal in a directory used to store the plot (e.g. repro-plots/7b). Copy the code from the text box in the "Custom controls" window to copy there the data from the emulations, then clear the text box in the "Custom controls" window.

To generate the plot, run:

```
../../plotting-scripts/plot-data.py --plot vary-rtt
```

The script simply reads the file path-congestion-probs.txt from each experiment, selects the line corresponding to the desired loss threshold (0.001, i.e. the first column in the file) and plots the path congestion probabilities (columns 2-5 in the file).

The plot is found in:

```
image-plot-7b-*/9. stats prob-cong-path - rtt.png
```

### Figure 7c  
After running the experiments, open a terminal in a directory used to store the plot (e.g. repro-plots/7c). Copy the code from the text box in the "Custom controls" window to copy there the data from the emulations, then clear the text box in the "Custom controls" window.

Unfortunately the script incorrectly places the two experiments in different directories. Move them to the same directory (it does not matter which one).

To generate the plot, run:

```
../../plotting-scripts/plot-data.py --plot vary-tcp
```

The script simply reads the file path-congestion-probs.txt from each experiment, selects the line corresponding to the desired loss threshold (0.001, i.e. the first column in the file) and plots the path congestion probabilities (columns 2-5 in the file).

The plot is found in:

```
image-plot-7c-*/10. stats prob-cong-path - tcp.png
```

### Figure 7d  
After running the experiments, open a terminal in a directory used to store the plot (e.g. repro-plots/7d). Copy the code from the text box in the "Custom controls" window to copy there the data from the emulations, then clear the text box in the "Custom controls" window.

To generate the plot, run:

```
../../plotting-scripts/plot-data.py --plot vary-transfer-size
```

The script simply reads the file path-congestion-probs.txt from each experiment, selects the line corresponding to the desired loss threshold (0.001, i.e. the first column in the file) and plots the path congestion probabilities (columns 2-5 in the file).

The plot is found in:

```
image-plot-7d-*/2. stats prob-cong-path - transferSize.png
```

### Figure 7e  
After running the experiments, open a terminal in a directory used to store the plot (e.g. repro-plots/7e). Copy the code from the text box in the "Custom controls" window to copy there the data from the emulations, then clear the text box in the "Custom controls" window.

To generate the plot, run:

```
../../plotting-scripts/plot-data.py --plot vary-rtt
```

The script simply reads the file path-congestion-probs.txt from each experiment, selects the line corresponding to the desired loss threshold (0.001, i.e. the first column in the file) and plots the path congestion probabilities (columns 2-5 in the file).

The plot is found in:

```
image-plot-7e-*/9. stats prob-cong-path - rtt.png
```

### Figure 7f  
After running the experiments, open a terminal in a directory used to store the plot (e.g. repro-plots/7f). Copy the code from the text box in the "Custom controls" window to copy there the data from the emulations, then clear the text box in the "Custom controls" window.

To generate the plot, run:

```
../../plotting-scripts/plot-data.py --plot vary-qos
```

The script simply reads the file path-congestion-probs.txt from each experiment, selects the line corresponding to the desired loss threshold (0.001, i.e. the first column in the file) and plots the path congestion probabilities (columns 2-5 in the file).

The plot is found in:

```
image-plot-7f-*/1. stats prob-cong-path - policing.png
```

### Figures 8a and 8b  
After running the experiments, open a terminal in a directory used to store the plot (e.g. repro-plots; do not create a subdirectory for the figure). Copy the code from the text box in the "Custom controls" window to copy there the data from the emulations, then clear the text box in the "Custom controls" window.

Note that there are two experiments; we are only interested in the experiment ending with "non-neutral-links-5-14-20". The other one contains an identical configuration except all links are neutral, but it was not included in the paper.

Open a terminal to the directory of the the experiment ending with "non-neutral-links-5-14-20". To run the inference algorithm and generate the plot, run:

```
../../../build-line-runner/line-runner --process-results $(pwd) numResamplings 3 lossThreshold 0.05
```

The image file for figure 8a is located in:

```
link-analysis-0.01/class-path-cong-probs-links.png
```

The image file for figure 8b is located in:

```
seq-analysis-*-lossth-0.05-*/link-seq-cong-prob-all-inferred.png
```
