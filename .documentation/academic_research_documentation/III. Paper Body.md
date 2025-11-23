TECHNOLOGICAL INSTITUTE OF THE PHILIPPINES
1338 Arlegui St. Quiapo, Manila

[3 spaces, Single Spaces with spaces after the paragraph]

A Final Project Submitted to the Department of Computer Engineering
In Partial Fulfillment of the Requirements for the Course CPE 408B - Emerging Technologies 2 in CpE 
for the degree of Bachelor of Science in Computer Engineering

[3 spaces, Single Spaces with spaces after the paragraph]

Gym Membership Management System (GyMMS)

[5 spaces, Single Spaces with spaces after the paragraph]

Submitted by:
Kit Kitaru


[5 spaces]



November 19, 2025

ACKNOWLEDGEMENT









TABLE OF CONTENTS

ACKNOWLEDGEMENT	2
TABLE OF CONTENTS	3
LIST OF FIGURES	5
LIST OF TABLES	6
ABSTRACT	7
1 EXECUTIVE SUMMARY	9
2 INTRODUCTION	11
2.1 Project Background	11
2.2 Client Overview	11
2.3 Project Objectives	11
2.4 Significance of the Project	12
2.5 Scope and Delimitations	12
3 SYSTEM ANALYSIS	13
2.1 Client Requirements	13
2.2 Functional Requirements	13
2.3 Non-Functional Requirements	13
2.4 Use Cases / User Stories	14
2.5 System Architecture	14
2.5.2 System Specifications	14
Table xx. Some Captions	14
4 DESIGN AND IMPLEMENTATION	15
3.1 Django Project Structure	15
Figure 3.1 Project Structure	16
Brief discussion of the 3.1	16
3.2 Forms and Validation	16
Figure 3.2 XXXXXXXX	16
3.3 Backend API	16
3.4 Web Application	17
3.4.1 Functional View	17
3.4.2 Database Design	17
3.4.3 Dataflow Diagram Level 0 and 1	17
3.4.4 User Interface and Features	17
5 TESTING AND DEBUGGING	18
4.1 Backend API Testing	18
4.2 Functionality Testing	19
Table 4.2 Sample Template	19
4.3 Debugging techniques and resolved issues	19
6 RESULTS AND ANALYSIS	20
7 CONCLUSIONS	21
5.1 Conclusion	21
5.2 Recommendations	22
5.3 Key Learnings	22
5.3 Challenges and Solutions	22
APPENDICES	23
A REFERENCES	24
B PROJECT MANAGEMENT	25
Project Manager / Team Members	25
Project Timeline / Schedule	25
Resources and Tools	25
Project Goals & Deliverables	25





LIST OF FIGURES









LIST OF TABLES








ABSTRACT


Purpose:





Methodology:





Results:






Conclusion:



1	EXECUTIVE SUMMARY
The executive summary serves as a concise overview of the project. It is written to give readers a clear understanding of the project’s objectives, scope, and significance without diving into technical details. Ideally, it should be crafted to engage both technical and non-technical audiences, highlighting the project’s value and impact.
Key Components in Paragraph Form (It should be written in 1 page, In paragraph form, not bullet or enumerated).

Introduction to the Project
Briefly introduce the project, its context, and the problem it aims to solve.
Example: “This project is an IoT-based system that utilizes an ESP8266 microcontroller to monitor environmental parameters such as temperature and humidity. It addresses the need for cost-effective and scalable solutions for real-time data acquisition and monitoring.”

Core Objectives
State the main goal of the project and its intended outcomes.
Example: “The primary objective is to provide an easy-to-use platform that allows users to monitor live and historical environmental data, enhancing decision-making in applications such as agriculture, smart homes, and industrial processes.”

Features and Functionality
Summarize the system’s main features in an integrated manner.
Example: “The system features real-time data collection using sensors, backend data processing through APIs, and visualization on a web application. The ESP8266 serves as the core hardware, while modern frameworks like Express.js and React are used for the backend and frontend.”

Benefits and Significance
Highlight the value the project delivers and its potential impact.
Example: “By combining affordable hardware with robust software, this project provides a cost-efficient solution for monitoring environmental conditions, making it accessible for diverse applications and paving the way for further IoT advancements.”








2	INTRODUCTION
2.1 Project Background
The fitness industry has been consistently growing worldwide, driven by increasing awareness of the importance of health and wellness. In 2023, the global fitness market was valued at over USD 96 billion, with projections indicating sustained growth through 2030 (Statista, 2024). This expansion highlights not only the rising demand for fitness services but also the need for more efficient administrative tools to manage gym operations. However, while large international fitness chains have adopted automated systems for membership and payment management, many smaller and community-based gyms continue to depend on manual processes.
In the Philippines, the fitness sector has similarly grown, particularly with the proliferation of small, community-based fitness centers and so-called “bakal gyms”—low-cost gyms that provide affordable access to strength training and exercise facilities (Chua, 2022). Unlike large commercial and high-end chains such as Anytime Fitness or Fitness First, these smaller gyms often operate with limited resources and rely heavily on manual processes for managing memberships, tracking payments, and monitoring member activity. While affordable and accessible, such manual systems are prone to inefficiencies, errors, and difficulties in scaling as membership numbers grow (Santos, 2021). This reliance on manual methods leads to inefficiencies such as human error, late renewals, and difficulties in record-keeping.
Manual recordkeeping methods, such as using notebooks or spreadsheets, create challenges in accuracy, timeliness, and data retrieval (Dela Cruz, 2020). Members may miss renewal dates, staff may struggle to update records efficiently, and payments are often limited to in-person transactions. This not only reduces convenience for clients but also restricts opportunities for gyms to adopt modern business models, such as flexible subscription plans or online payment gateways (World Health Organization, 2021).
Globally, digital transformation in the fitness industry has been accelerated by the COVID-19 pandemic, which underscored the value of integrating technology into health and fitness services (Chen & Chen, 2021). Many international studies emphasize that adopting digital platforms improves efficiency, reduces administrative workload, and enhances customer satisfaction (Lee, 2019; Deloitte, 2022). However, these technological advancements are unevenly distributed, with small and independent gyms often lagging behind due to cost constraints, lack of technical expertise, or absence of tailored solutions (Tan, 2023).
In this context, the Gym Membership Management System (GyMMS) is proposed as a practical and affordable solution for local gym owners in the Philippines. Powered by Django, GyMMS seeks to automate key processes such as subscription tracking, payment monitoring, and member activity metrics, thereby reducing reliance on manual methods. By addressing the unique needs of small-scale and ‘bakal’ gyms, GyMMS aims to bridge the digital divide, empower gym owners with efficient tools, and contribute to the overall modernization of the Philippine fitness industry.


2.2 Client Overview
The client is a local or ‘bakal’ gym owner who manages a fitness center near his community. He has been running his establishment for several years and caters primarily to neighborhood residents, fitness novices, and even students that are seeking affordable access to fitness and strength training facilities. Unlike large and high-end commercial gyms, the client operates with limited resources and relies heavily on traditional methods of administration.
Membership management is handled manually. The client records member names and start dates in a notebook, occasionally transferring details to basic Excel sheets. Subscription monitoring depends on manually checking these notes and records, which is time-consuming and prone to being forgotten to monitor. Payments are strictly in-person, with the client relying on the honesty of members to settle dues on time. This trust-based system, while rooted in strong community ties and bonds, often results in delayed or missed payments that affect the gym’s cash flow.
Despite these limitations, the client is committed to maintaining the accessibility and affordability of his local gym. He recognizes the importance of improving efficiency in his operations but lacks exposure to digital tools that could automate membership and payment processes. A streamlined, user-friendly system would help the client reduce administrative burdens, improve accuracy, and strengthen member retention without compromising the personal and community-driven environment that defines his gym.



2.3 Project Objectives
The general objective of this project is to design and develop a Gym Membership Management System (GyMMS) that will automate and ease the management of gym member subscriptions, payment tracking, and record-keeping. The system aims to replace the client’s traditional reliance on manual methods such as notebooks and spreadsheets with a digital platform that enhances accuracy, efficiency, and accessibility. By doing so, the project seeks to provide a convenient and reliable tool for both the gym owner or the Client and its gym members, ensuring timely updates on membership status, secure payment handling, and simplified monitoring of client records.

Specific Objectives
SO1: Develop a membership dashboard that displays subscription status, member details, start and end dates, and membership duration.
SO2: Implement an analytics dashboard that provides data visualization for sales, revenue, and membership trends.
SO3: Integrate online payment solutions through multiple local payment APIs (e.g., GCash, GoTyme, InstaPay) to allow secure and convenient digital transactions.




2.4 Significance of the Project
The Gym Membership Management System (GyMMS) is proposed as a web-based application built on the Django framework which will address the inefficiencies in manual gym operations. The system will provide gym owners such as the Client with tools to automate membership tracking, monitor subscription expirations, process payments, and record member activity metrics. By replacing traditional notebooks and spreadsheets, GyMMS aims to reduce human error, improve accuracy, and enhance convenience for both gym owners such as the Client and gym members.
Through GyMMS, the client will be able to view and manage all member subscriptions in a centralized dashboard, reducing the reliance on notebooks and spreadsheets. Automated reminders will remind members of upcoming renewals, minimizing late payments and improving retention. To further support the gym’s financial operations, the system will integrate with local online payment platforms such as GCash, GoTyme, and InstaPay, enabling secure and convenient digital transactions.
Additionally, GyMMS will include analytics and visualization tools to help the client track revenue, monitor membership trends, and make data-driven business decisions. By combining ease of use, affordability, and scalability, the system will empower local gym owners to modernize their operations without losing the community-based and personal environment that defines their establishments.



2.5 Scope and Delimitations
Direction: List the scope and delimitations of the project






3	SYSTEM ANALYSIS

2.1 Client Requirements
The client requires the system to address the current challenges of manual tracking and limited payment options. The following requests were identified:
A reliable system to track memberships without relying on notebooks or spreadsheets.
A dashboard that provides visibility of members’ subscription details and renewal dates.
Automated reminders for upcoming or overdue payments.
Clear and simple reports for sales and revenue monitoring.
Integration with local online payment options (e.g., GCash, GoTyme, InstaPay).
A user-friendly and secure platform that requires minimal technical expertise.



2.2 Functional Requirements
—------
—------
—------


2.3 Non-Functional Requirements
—------
—------
—------



2.4 Use Cases / User Stories
Provide figures, illustrations, etc.

2.5 System Architecture
Provide figures, illustrations, etc.



2.5.2 System Specifications
The System Specifications section defines the technical requirements and performance metrics of the entire project. It describes the system’s operational parameters, capabilities, and limitations, serving as a blueprint for understanding its functionality. This section ensures that the project’s scope and technical achievements are clearly documented, providing a baseline for evaluation and replication.
A tabular format can be used to summarize the specifications for clarity. An example is given below:

Table xx. Some Captions
Specification
Details
System Name
IoT-Based Environmental Monitoring System
Purpose
Real-time temperature and humidity monitoring
Data Collection Frequency
1 sample per second
Data Transmission Protocol
HTTP for API communication
Operating Voltage
3.3V for microcontroller, 5V for peripherals
System Latency
Average response time of 500ms
Network Requirements
2.4 GHz Wi-Fi
Storage Capacity
1 GB database for historical data storage
User Interface
Web application with real-time data visualization
Scalability
Supports up to 50 devices simultaneously

Some Discussions on Specifications as summary






4	DESIGN AND IMPLEMENTATION
4.1 Django Project Structure
Provide figures, illustrations, etc.

Figure 4.1 Project Structure
Brief discussion of the 3.1


4.2 Forms and Validation
Provide figures, illustrations, etc.
Figure 4.2 XXXXXXXX



4.3 Backend API
Provide discussion, figures, illustrations, etc.


4.4 Web Application
Provide concise discussion


4.4.1 Functional View
WIREFRAME
Provide discussion, figures, illustrations, etc.


4.4.2 Database Design
Provide discussion, figures, illustrations, etc.


4.4.3 Dataflow Diagram Level 0 and 1
Provide discussion, figures, illustrations, etc.
4.4.4 User Interface and Features
Provide discussion, figures, illustrations, etc.





5	TESTING AND DEBUGGING
5.1 Backend API Testing
Provide discussion, figures, illustrations, tables etc.


5.2 Functionality Testing
UI/UX testing and End-to-end system testing.

Table 5.2 Sample Template
Feature
Test Input
Expected Output
Actual Output
Status
Registration
Valid input
Account created




Login
Correct credentials
Redirect to dashboard




Profile Update
Valid input
Updated successfully




Logout
Click logout
Redirect to login



Provide discussion on Table 4.2


5.3 Debugging techniques and resolved issues
Provide discussion and proofs




6	RESULTS AND ANALYSIS
The Results and Analysis section presents the outcomes of the project and evaluates its performance against the initial objectives. This section should narrate the findings from testing and deployment, supported by data, charts, and graphs to illustrate the results. The focus is on interpreting the data, identifying trends, and drawing conclusions about the system's effectiveness.
Begin by summarizing the data collected during testing or real-world operation, explaining its relevance to the project goals. Discuss key metrics, such as accuracy, response time, or system reliability, and compare them to expected values or benchmarks. Use charts and graphs to visualize the data, such as bar graphs for performance metrics or line charts for trends over time.
Analyze the data by explaining what the results indicate about the system’s functionality and usability. Highlight any patterns, anomalies, or areas where the system exceeded or fell short of expectations. Provide explanations for the observed outcomes, such as how design choices or external factors influenced performance.
Include images or diagrams that support the analysis, such as screenshots of the system in operation or annotated test results. These visuals not only add clarity but also make the documentation more engaging and accessible. The narrative should connect the results back to the project objectives, providing a comprehensive assessment of the system's success and areas for potential improvement.



7	CONCLUSIONS
7.1 Conclusion
Provide discussion


7.2 Recommendations
Provide discussion


7.3 Key Learnings
Provide discussion


7.3 Challenges and Solutions
Provide discussion





APPENDICES



A	REFERENCES

Should be in APA format.








B	PROJECT MANAGEMENT
Team Members
Direction: List the names, roles, and responsibilities of each member.



Project Timeline / Schedule
Direction: Provide a Gantt chart or table of planned activities and duration.



Resources and Tools




Project Goals & Deliverables
Direction: Summarize what the team aims to accomplish and deliver to the client.





C	SOURCE CODE

---

PROJECT RUBRIC
Criteria
4 - Exceptional
3 - Proficient
2 - Developing
1-Needs Improvement
Score
Relevance and Innovation
Highly innovative application of IoT in aquaculture, solving a significant problem with a clear and meaningful solution.
Effective IoT application addressing a relevant aquaculture problem, showing moderate creativity.
Limited IoT application, addressing a generic or poorly defined problem.
Minimal or unclear relevance to aquaculture, with no meaningful use of IoT.
 
Technical Implementation
Fully functional system with seamless integration of hardware, software, and communication, demonstrating reliability and excellent performance.
Functional system with minor issues, good integration, and satisfactory performance in testing.
Partially functional system with gaps in integration or performance.
System is largely non-functional, with major technical issues or missing components.
 
Documentation and Presentation
Clear, comprehensive, and professional documentation, with well-organized sections and visuals. Polished presentation via video and GitHub.
Clear and complete documentation with minor issues in organization or visuals. Presentation is adequate and informative.
Documentation lacks clarity or is incomplete, with minimal use of visuals. Presentation lacks detail or clarity.
Poorly organized or missing documentation, with minimal or uninformative presentation.


Testing and Results
Comprehensive testing with detailed analysis, supported by meaningful charts and graphs, showing reliability and effectiveness.
Adequate testing demonstrating reliability, with some analysis and supporting visuals.
Limited or incomplete testing, with minimal analysis or visuals.
Minimal or absent testing, with no meaningful analysis or evidence of results.


Develop appropriate experimentation
The students are able to develop a lab experiment/activity appropriate to the chosen topic and aligned to the engineering principles learned in the previous experiments. The developed lab experiment/activity has a complete presentation of block/schematic diagram, provided the use of modern tools and techniques, and integrated principles/discussions that were based on proven studies.
The students are able to develop components of a laboratory experiment appropriate to the chosen topic and aligned to the engineering principles learned in the previous experiments 
The students are able to develop component of a laboratory experiment but has no presentations of analysis of data yet has presented conclusion or recommendation
The students are unable to develop a basic component of a laboratory experiment.


Conduct appropriate experimentation
The students are able to conduct appropriate laboratory experiment/activity with sufficient results and able draw a valid conclusion
The students are able to conduct appropriate laboratory experiment/activity with sufficient results and able draw a valid conclusion
The students conduct some laboratory experiments/activities
but did not arrive at the correct results
The students are unable to conduct a laboratory experiment/activity.


Protocol to conduct an experiment
Develop a protocol to conduct an experiment  and members follow good and safe laboratory practice at all times in the conduct of experiments.
Develop a protocol to conduct an experiment exceeding the requirements
The students are able to determine the objectives of the experiment or test to be performed but fail to identify test to performed
The students failed to determine the objectives of the experiment or test to be performed.




Ability to analyze and interpret data


The students use multiple data analysis techniques appropriate for data collected, informative with respect to the experimentation/activity being conducted. Data analysis is reported with comprehensive interpretation.
The students use adequate data analysis techniques appropriate for data collected, informative with respect to the experimentation/activity being conducted. Data analysis is reported with sufficient interpretation.
The students provide limited analysis of data with no interpretation.
The students are unable to provide analysis and interpretation of data.


Use of engineering judgment to draw conclusions
The student was able to use engineering judgement*  more than sufficient to draw correct conclusions and was able to provide new insights.


The student was able to use engineering judgement more than sufficient to draw correct conclusions.
The student was able to use engineering judgement but insufficient to draw correct conclusions.
The student failed to use engineering judgement to draw conclusions.




Total Score
	Percentage rating = (Total Score/36) x 100

Evaluated by:													
							
_________________________________________					_____________________				 Printed Name and Signature of Faculty Member			   			Date


