\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts
% The preceding line is only needed to identify funding in the first footnote. If that is unneeded, please comment it out.
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em
    T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}
\begin{document}

\title{AirBnB 
\thanks{Identify applicable funding agency here. If none, delete this.}
}

\author{\IEEEauthorblockN{Rafi Putra Abdurrahman}
\IEEEauthorblockA{\textit{AI and Data Engineering} \\
\textit{Istanbul Technical University}\\
Istanbul, Turkey \\
abdurrahmanr23@itu.edu.tr}
\and
\IEEEauthorblockN{Kuanysh Otegen}
\IEEEauthorblockA{\textit{AI and Data Engineering} \\
\textit{Istanbul Technical University}\\
Istanbul, Turkey \\
otegen22@itu.edu.tr}
\and
\IEEEauthorblockN{Emre Demirci}
\IEEEauthorblockA{\textit{AI and Data Engineering} \\
\textit{Istanbul Technical University}\\
Istanbul, Turkey \\
demirciem22@itu.edu.tr}\and
\IEEEauthorblockN{Nikolas Leka}
\IEEEauthorblockA{\textit{AI and Data Engineering} \\
\textit{Istanbul Technical University}\\
Istanbul, Turkey \\
leka23@itu.edu.tr}
}

\maketitle

\section{Introduction}

Modern data-driven platforms usually depend heavily on scalable data engineering systems to collect, process and analyse large volumes of data generated from user interactions. Companies such as Airbnb continuously generate data from listings, user behaviour and transactions, which must be efficiently ingested, transformed and then stored to support analytics and decision making. our project presents a miniaturized version of such a system by designing and implementing and end-to-end engineering pipeline for Airbnb listing data. The pipeline we aim to deliver intends to integrate multiple widely used tools withing a containerized environment, enabling automated data ingestion, processing, storage and visualization. By reproducing key architectural principles of a real world systems at a smaller scale, we aim to demonstrate practical understanding of modern data engineering workflows.
\section{Problem Description}

Even though structured datasets such as Airbnb listings are available and easily accessible, transforming raw data into meaningful insights requires a well designed pipeline that ensures data quality, consistency and accessibility. Raw datasets are often static and incomplete or even not suitable for analytical use, therefore without a proper ingestions, transformation and orchestration mechanism, these datasets cannot support real-time or even near real-time analysis. The challenge addressed in this project is to design a reproducible and containerized data pipeline that simulates real-world data flow, from raw data ingestion to outputs ready for analytics. This includes handling data preprocessing, schema design, workflow orchestration and integration with search and visualization tool. Each of the mentioned steps will be explained with details in our Methodology section. Our objective is to bridge the gap between raw data and actionable insights by building a system that reflects the architecture and operational considerations of modern data platforms.


\section{Methodology}

The proposed system implements an end-to-end data engineering pipeline to simulate Airbnb's data workflow. The pipeline processes Airbnb listing data through a sequence of ingestion, transformation, storage, indexing, and visualization stages, all deployed within Docker to ensure reproducibility.

The workflow begins with a CSV dataset, which is ingested using Apache NiFi. Although the dataset is static, NiFi is configured to simulate batch ingestion by periodically reading and forwarding data, mimicking real-world data arrival. Following ingestion, Apache Airflow orchestrates the processing pipeline using Directed Acyclic Graphs (DAGs), ensuring proper task scheduling and dependency management. Within this stage, the data will be cleaned and transformed, including handling missing values, removing inconsistencies, and standardizing formats.

The processed data is then stored in PostgreSQL, where a structured schema is applied to maintain consistency and enable efficient querying. To support fast search and analytical capabilities, the data is subsequently indexed into Elasticsearch. This allows for flexible querying, aggregation, and fast data exploration.

Finally, Kibana is used to visualize the indexed data through interactive dashboards, providing insights such as price distributions, geographic patterns, and listing characteristics.


