# Workshop Service Monitoring Tool

A Python-based workshop tool that simulates a financial trading venue with mock services.

## Requirements

Python 3.12 is recommended to run this tool.

For Windows users once you have installed Python 3.12 you can use it directly.
If required you can specify an alias for `python3` to ensure the correct version is used for Mac/Linux by using the following command on the terminal.

```bash
alias python3=python3.12
```

## 🌱 The Journey Begins

### Setup

```bash
git clone <repository-url>/workshop-svc
cd workshop-svc
```

Run the following command for validation that you are ready to start the workshop. You should see a service dashboard.

```bash
python3 workshop.py status      # Show all services
```

After completion let's pause together and wait for the presentation to continue with Checkpoint 1.

---

## 🌱 Checkpoint 1 - The Hunt for Hidden Waste

Start by exploring the system’s health and historical metrics.

```bash
python3 workshop.py status                          # System health
python3 workshop.py historical fax-service        # Historical data
```

You might have noticed a note about "Low utilization on large machine" in the `python3 workshop.py status` recommendation, and another one mentioning "Service is unused - remove from deployment.yaml to free resources" in the `python3 workshop.py historical fax-service` command.

To make changes to the deployments of services then you can edit the `deployment.yaml` file.

```bash
workshop-svc/
├── 📁 src/                       # Main folder
│   ├── 📁 configuration_files/
│   │   ├── deployment.yaml        # Service deployment configuration
```

To get further clues and/or test whether your solution worked:

```bash
python3 workshop.py validate --checkpoint 1
```

Great work! You have completed the first optimization by removing the unused fax-service, please wait for the presentation to continue with Checkpoint 2.

---

## 🌱 Checkpoint 2 - Clean Code, Clean Planet

Now we will dive into the system's metrics and code to understand what is slowing it down.

```bash
# Show detailed utilization metrics
python3 workshop.py checkpoint 2 run-market-data    # Test performance
python3 workshop.py latency                         # Check latency
python3 workshop.py status                          # System health
```

After reading the recommendations from the `python3 workshop.py status` and `python3 workshop.py latency` commands review the code and apply optimization in the function `getMarketData(api_client)` located in `get_market_data.py`.

```bash
workshop-svc/
├── 📁 src/                       # Main folder
│   ├── get_market_data.py         # Market data fetching
```

To get further clues or test whether your solution worked:

```bash
python3 workshop.py validate --checkpoint 2
```

Once you have made your changes and validated, re-run the performance test command to see the improvements.

```bash
python3 workshop.py checkpoint 2 run-market-data   # Test performance
```

You have now completed the Python code optimization by using a bulk api in the market dataloading code, please wait for the presentation to continue with Checkpoint 3.

---

## 🌱 Checkpoint 3 - Green Light, Go Time

Finally let's review the batch job schedule and analyze environmental impact to ensure optimal scheduling of workloads.

```bash
python3 workshop.py scheduler                       # Check job scheduling
python3 workshop.py carbon                          # Carbon impact dashboard
```

```bash
workshop-svc/
├── 📁 src/                       # Main folder
│   ├── 📁 configuration_files/
│   │   └── schedule.yaml          # Job scheduling configuration
```

Now make changes to the `schedule.yml` file for the start_time to be run at different times and at low carbon periods (2-6AM) for each job to reduce carbon impact.

Review your changes with the following commands.

```bash
python3 workshop.py scheduler
python3 workshop.py validate --checkpoint 3
```

You have optimized the sustainable scheduling task by running at low carbon times and non conflicting hours, please wait for the presentation to continue with Checkpoint 4.

---

## 🌱 Checkpoint 4 - How Green is your Code?

As we have progressed through the exercises, we can measure the sustainability improvements made to the system using the Software Carbon Intensity (SCI) metric.

```bash
python3 workshop.py software-carbon-intensity
```

This dashboard shows the breakdown of each component of the Software Carbon Intensity (SCI) formula. Along with how each optimization has improved the overall SCI score of the system.

You have now completed the workshop, well done!

### 🛠 Restore Checkpoints

If you run into issues at any point, use the commands below to reset your files back to the starting state of a checkpoint.

```bash
python3 workshop.py backup restore-checkpoint1-start # Go back to Checkpoint 1
python3 workshop.py backup restore-checkpoint2-start # Go back to Checkpoint 2
python3 workshop.py backup restore-checkpoint3-start # Go back to Checkpoint 3
```

## Usage

This workshop tool is a toy simulation created solely for educational and demonstration purposes within the context of this workshop. It is not representative of any real systems, services, data, or practices of Bloomberg.

The tool simulates a financial trading venue and its related services in a mock environment. All values, configurations, transactions, and service behaviors are entirely fictional and not connected to any live or production systems.

Nothing generated, displayed, or executed by this tool should be interpreted as real, accurate, or reflective of Bloomberg's actual infrastructure or operations.

All data and metrics, including service activity, performance values, and alerts, are randomly generated for educational purposes and do not represent real measurements, benchmarks, or recommendations. Any resemblance to real systems or values is purely coincidental.

This environment is designed solely to simulate realistic scenarios and demonstrate principles of sustainable and efficient software design.

Use of this tool should be limited to the scope of the workshop and it is provided “as is,” without any guarantees of accuracy, reliability, or suitability for real-world financial applications.

## License

Distributed under the Apache 2.0 license.
See [LICENSE](LICENSE) for more information.

## Acknowledgements

This README was adapted from Bloomberg's [open source project template](https://github.com/bloomberg/oss-template).
