<a name="readme-top"></a>
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![Cisco Sample Code License, Version 1.1][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/jasoncdavis/SSH2Influx">
    <img src="images/logo-SSH2Influx.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">SSH2Influx</h3>

  <p align="center">
    Convert CLI-based data from SSH-accessible endpoints into InfluxDB measurements for graphing and dashboards!

    <br />
    <a href="https://github.com/jasoncdavis/SSH2Influx"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/jasoncdavis/SSH2Influx">View Demo</a>
    ·
    <a href="https://github.com/jasoncdavis/SSH2Influx/issues">Report Bug</a>
    ·
    <a href="https://github.com/jasoncdavis/SSH2Influx/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![NOC Dashboard Screen Shot][product-screenshot]]

Have you ever needed to extract data from a device using SSH, then put it into InfluxDB to create beautiful Grafana dashboards?  If so, this is the project for you!  Admittedly there are *much better* ways to programmatically extract data from networked devices - gRPC streaming telemetry, NETCONF RPCs, even SNMP!  However, sometimes there's a metric in that device that is only available through an SSH connection and some command execution.

This project enabled you to define what networked devices should be accessed, what commands to execute (either as a group or individually), what regular expression (regex) patterns to use to capture the desired output AND how to define the Influx tagging and keying to make proper measurements that are injected into InfluxDB!  How cool is that!?

A parameters file defines the device list, commands, regex patterns and tagging/keying specifications.
A separate optionconfig.yaml file defines the secret credentials that should be maintained separately.

You may have multiple parameters files and use them at different polling intervals to suite your needs.

This SSH2Influx project has been used for the last year at the CiscoLive NOC to collect CLI-based metrics from Wireless LAN Controllers (WLCs) and Catalyst 7k and 9k switches.  It has recently been enhanced to also support Linux end-points, such as Ubuntu VMs.
<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Python][python.org]][Python-url]
* [![InfluxDB][influxdb.org]][Influx-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```

### Installation

1. Get a free API Key at [https://example.com](https://example.com)
2. Clone the repo
   ```sh
   git clone https://github.com/jasoncdavis/SSH2Influx.git
   ```
3. Install NPM packages
   ```sh
   npm install
   ```
4. Enter your API in `config.js`
   ```js
   const API_KEY = 'ENTER YOUR API';
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature

See the [open issues](https://github.com/jasoncdavis/SSH2Influx/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Your Name - [@SNMPguy](https://twitter.com/SNMPguy) - jadavis@cisco.com

Project Link: [https://github.com/jasoncdavis/SSH2Influx](https://github.com/jasoncdavis/SSH2Influx)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/jasoncdavis/SSH2Influx.svg?style=for-the-badge
[contributors-url]: https://github.com/jasoncdavis/SSH2Influx/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/jasoncdavis/SSH2Influx.svg?style=for-the-badge
[forks-url]: https://github.com/jasoncdavis/SSH2Influx/network/members
[stars-shield]: https://img.shields.io/github/stars/jasoncdavis/SSH2Influx.svg?style=for-the-badge
[stars-url]: https://github.com/jasoncdavis/SSH2Influx/stargazers
[issues-shield]: https://img.shields.io/github/issues/jasoncdavis/SSH2Influx.svg?style=for-the-badge
[issues-url]: https://github.com/jasoncdavis/SSH2Influx/issues
[license-shield]: https://img.shields.io/badge/License-Cisco%20Sample%20Code%20License%2C%20Version%201.1-lime
[license-url]: https://developer.cisco.com/site/license/cisco-sample-code-license
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/jasoncdavis
[product-screenshot]: images/screenshot.jpg

[python.org]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://python.org/
[influxdb.com]: https://img.shields.io/badge/InfluxDB-22ADF6?style=for-the-badge&logo=InfluxDB&logoColor=white
[Python-url]: https://www.influxdata.com/products/influxdb-overview/