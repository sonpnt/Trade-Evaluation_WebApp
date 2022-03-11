# WebApp: Trade Evaluation
[**Quickstart**](#quickstart-colab-in-the-cloud)
| [**Transformations**](#transformations)
| [**Install guide**](#installation)
| [**Neural net libraries**](#neural-network-libraries)
| [**Change logs**](https://jax.readthedocs.io/en/latest/changelog.html)
| [**Reference docs**](https://jax.readthedocs.io/en/latest/)

"Hello World" 




is a [Cloud Run](https://cloud.google.com/run/docs) application that renders a simple webpage.

For details on how to use this sample as a template in Cloud Code, read the documentation for Cloud Code for [VS Code](https://cloud.google.com/code/docs/vscode/quickstart-cloud-run?utm_source=ext&utm_medium=partner&utm_campaign=CDR_kri_gcp_cloudcodereadmes_012521&utm_content=-) or [IntelliJ](https://cloud.google.com/code/docs/intellij/quickstart-cloud-run?utm_source=ext&utm_medium=partner&utm_campaign=CDR_kri_gcp_cloudcodereadmes_012521&utm_content=-).

### Table of Contents
* [Getting Started with VS Code](#getting-started-with-vs-code)
* [Getting Started with IntelliJ](#getting-started-with-intellij)
* [Sign up for User Research](#sign-up-for-user-research)

---
## Quickstart: Colab in the Cloud

### Run the app locally with the Cloud Run Emulator
1. Click on the Cloud Code status bar and select 'Run on Cloud Run Emulator'.  
![image](https://https://sphanfinance.com/statics/img/status-bar.png)

2. Use the Cloud Run Emulator dialog to specify your [builder option](https://cloud.google.com/code/docs/vscode/deploying-a-cloud-run-app#deploying_a_cloud_run_service). Cloud Code supports Docker, Jib, and Buildpacks. See the skaffold documentation on [builders](https://skaffold.dev/docs/pipeline-stages/builders/) for more information about build artifact types.  
![image](https://https://sphanfinance.com/statics/img/build-config.png)

3. Click ‘Run’. Cloud Code begins building your image.

4. View the build progress in the OUTPUT window. Once the build has finished, click on the URL in the OUTPUT window to view your live application.  
![image](./img/cloud-run-url.png)

5. To stop the application, click the stop icon on the Debug Toolbar.
## Transformations

