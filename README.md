<h1 align="center">
  Multimodal Unlearning Across Vision, Language, Video, and Audio: Survey of Methods, Datasets, and Benchmarks
</h1>

<div align="center">
<a href="https://doi.org/10.36227/techrxiv.176945748.88280394/v1"><img src="https://img.shields.io/badge/DOI-TechRxiv-1f77b4?style=for-the-badge&logo=ieee&logoColor=white"></a>&nbsp;<!--
--><a href="https://www.techrxiv.org/"><img src="https://img.shields.io/badge/Paper-TechRxiv-ff7f0e?style=for-the-badge&logo=arxiv&logoColor=white"></a>&nbsp;<!--
--><a href="https://github.com/smsnobin77/Awesome-Multimodal-Unlearning/pulls"><img src="https://img.shields.io/badge/PRs-welcome-2ca02c?style=for-the-badge&logo=github&logoColor=white"></a>
</div>
&nbsp;
                                                                                 
> **Authors**: Nobin Sarwar<sup>🏫</sup>, Shubhashis Roy Dipta<sup>🏫</sup>, Zheyuan Liu<sup>🎓</sup>, Vaidehi Patil<sup>🏛️</sup>  
>
> **Affiliations**: <sup>🏫</sup> University of Maryland, Baltimore County &nbsp;·&nbsp; <sup>🎓</sup> University of Notre Dame &nbsp;·&nbsp; <sup>🏛️</sup> UNC Chapel Hill

> We welcome issues for any related work not discussed and will consider inclusion in future updates.

## 🎉 Latest News

- **[2026-02-14]** 🚀 We launch the **Awesome Multimodal Unlearning** repository to track methods, datasets, and benchmarks. Check it out: [GitHub](https://github.com/smsnobin77/Awesome-Multimodal-Unlearning)  
- **[2026-01-26]** 📄 Our survey on **Multimodal Unlearning** is released on TechRxiv. See the paper: [TechRxiv](http://dx.doi.org/10.36227/techrxiv.176945748.88280394/v1)

## 📌 Citation

If our work supports your research or applications, we would appreciate a ⭐ and a citation using the BibTeX below.

```bibtex
@article{sarwar2026mm-unlearning-survey,
  title = {{Multimodal Unlearning Across Vision, Language, Video, and Audio: Survey of Methods, Datasets, and Benchmarks}},
  author = {Sarwar, Nobin and Roy Dipta, Shubhashis and Liu, Zheyuan and Patil, Vaidehi},
  year = {2026},
  doi = {10.36227/techrxiv.176945748.88280394/v1},
  url = {https://doi.org/10.36227/techrxiv.176945748.88280394/v1},
  publisher = {Institute of Electrical and Electronics Engineers (IEEE)},
  month = jan
}
```

## 📚 Contents  
- [Latest News](#-latest-news)
- [Citation](#-citation)
- [Overview](#-overview)
- [Comparison with Existing Surveys](#-comparison-with-existing-surveys)
- [Taxonomy of Multimodal Unlearning](#-taxonomy-of-multimodal-unlearning)
- [Benchmarks for Multimodal Unlearning](#-benchmarks-for-multimodal-unlearning)
- [Evaluation Metrics](#-evaluation-metrics)
- [Applications of Multimodal Unlearning](#-applications-of-multimodal-unlearning)
- [Curated Paper List](#-curated-paper-list)
- [Contact](#-contact)

## 🧭 Overview  

Multimodal unlearning requires identifying effective intervention points within the model pipeline. Figure 2 illustrates methods spanning data-side, training-time, architecture-constrained, and decoding-time stages, producing an updated model (MFM′). Training-free approaches instead apply direct parameter or representation edits (Δ).

<p align="center">
  <img src="assets/multimodal-unlearning-taxonomy.png" width="50%" />
  <br/>
  <span style="font-size: 10px;">Figure 2: <b>System-level intervention points</b> for multimodal unlearning across the model pipeline.</span>
</p>

## 📊 Comparison with Existing Surveys

<p align="center">
  <img src="assets/table-1.png" width="50%"/>
  <br/>
  <span style="font-size: 10px;">Table 1: Comparison of multimodal unlearning surveys <br> across <b>modalities</b> and <b>system-first taxonomy</b> coverage.</span>
</p>

While several surveys address multimodal unlearning (Table 1), most focus on unimodal or limited text–image settings, and adopt algorithm-centric taxonomies that obscure practical intervention points. **A unified cross-modal perspective remains lacking**; key references are listed below. 

- **Si et al., 2023** — Knowledge Unlearning for LLMs: Tasks, Methods, and Challenges [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2311.15766)

- **Blanco-Justicia et al., 2025** — Digital Forgetting in Large Language Models: A Survey of Unlearning Methods [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2404.02062)

- **Liu et al., 2024f** — Machine Unlearning in Generative AI: A Survey [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2407.20516)

- **Liu et al., 2025b** — Rethinking Machine Unlearning for Large Language Models [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2402.08787)

- **Feng et al., 2025b** — A Survey on Generative Model Unlearning: Fundamentals, Taxonomy, Evaluation, and Future Direction [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2507.19894)

- **Geng et al., 2025b** — A Comprehensive Survey of Machine Unlearning Techniques for Large Language Models [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2503.01854)


## 📂 Taxonomy of Multimodal Unlearning

We organize multimodal unlearning via a **system-first taxonomy** across **five** intervention stages:

- **Data-Side Interventions (Section 3.1)** – Modify inputs or data distributions to reduce learnability of target content.  
- **Training-Time Edits (Section 3.2)** – Update model parameters to suppress target behavior.  
- **Architecture-Constrained Unlearning (Section 3.3)** – Localized updates within layers or structures.
- **Training-Free Unlearning (Section 3.4)** – Apply closed-form parameter or representation edits without retraining.  
- **Decoding-Time Unlearning (Section 3.5)** – Control generation without modifying model parameters.  

<p align="center">
  <img src="assets/figure-1.png" width="70%"/>
  <br/>
  <span style="font-size: 10px;">Figure 1: Taxonomy of multimodal unlearning by <b>intervention stage</b> and <b>control pathway</b>.</span>
</p>

## 📈 Benchmarks for Multimodal Unlearning  

We organize representative multimodal unlearning benchmarks into **three** categories: **unified suites**, **identity and privacy**, and **content and knowledge**, based on their targets and evaluation focus (Table 3).

**🧪 Unified Benchmark Suites**
- MU-Bench: A Multitask Multimodal Benchmark for Machine Unlearning [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2406.14796)

- Protecting Privacy in Multimodal Large Language Models with MLLMU-Bench [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2410.22108)

- PEBench: A Fictitious Dataset to Benchmark Machine Unlearning for Multimodal Large Language Models [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2503.12545)

- UMU-Bench: Closing the Modality Gap in Multimodal Unlearning Evaluation [![OpenReview](https://img.shields.io/badge/OpenReview-8c1d18?style=flat-square&logo=openreview&logoColor=white)](https://openreview.net/pdf?id=M476xkfNXe)

**🔐 Identity and Privacy Unlearning**
- CLEAR: Character Unlearning in Textual and Visual Modalities [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2410.18057)

- Benchmarking Vision Language Model Unlearning via Fictitious Facial Identity Dataset [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2411.03554)

- Alexa, can you forget me? Machine Unlearning Benchmark in Spoken Language Understanding [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2505.15700)

**📚 Content and Knowledge Unlearning**
- A Dataset and Benchmark for Copyright Infringement Unlearning from Text-to-Image Diffusion Models [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2403.12052)

- UnlearnCanvas: Stylized Image Dataset for Enhanced Machine Unlearning Evaluation in Diffusion Models [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2402.11846)

- Holistic Unlearning Benchmark: A Multi-Faceted Evaluation for Text-to-Image Diffusion Model Unlearning [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2410.05664)

- Six-CD: Benchmarking Concept Removals for Text-to-image Diffusion Models [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2406.14855)

- Single Image Unlearning: Efficient Machine Unlearning in Multimodal Large Language Models [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2405.12523)

- Unlearning Sensitive Information in Multimodal LLMs: Benchmark and Attack-Defense Evaluation [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2505.01456)

- SafeEraser: Enhancing Safety in Multimodal Large Language Models through Multimodal Machine Unlearning [![arXiv](https://img.shields.io/badge/arXiv-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/pdf/2502.12520)
  
## 📏 Evaluation Metrics  

Evaluation uses metric suites that assess forgetting, utility retention, robustness, and efficiency, as summarized in **Figure 3**. We defer detailed metric definitions and evaluation protocols to **Appendix C**.

<p align="center">
  <img src="assets/figure-3.png" width="50%" />
  <br/>
  <span style="font-size: 10px;">Figure 3: Evaluation dimensions and representative metrics for multimodal unlearning.</span>
</p>

## 🧩 Applications of Multimodal Unlearning  

Multimodal unlearning enables selective removal of specific identities, attributes, or concepts without full retraining while preserving overall capability and stability. Detailed use cases and representative studies are provided in **Appendix F**.

<p align="center">
  <img src="assets/multimodal-unlearning-applications.png" width="60%" />
  <br/>
  <span style="font-size: 10px;">Figure 4: Core application scenarios of multimodal unlearning.</span>
</p>


## 📑 Curated Paper List  


## 📧 Contact

This repository is actively maintained and continuously updated 🚀. If you notice any issues or would like your work on Multimodal Unlearning included, please open an issue or contact us via email.

**Corresponding author:** Nobin Sarwar (smsarwar96@gmail.com)
