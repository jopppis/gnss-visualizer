<a name="readme-top"></a>
<!-- README.md based on https://github.com/othneildrew/Best-README-Template -->


[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![AGPL-3.0 License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<br />
<div align="center">
  <a href="https://github.com/jopppis/gnss-visualizer">
    <img src="https://github.com/jopppis/gnss-visualizer/assets/25751262/da2d0ab8-140d-44bc-a8bf-407bed7b97d4" alt="Logo">
  </a>

  <h3 align="center">GNSS Visualizer</h3>

  <p align="center">
    Interactive analysis of GNSS data!
    <br />
    <br />
    <a href="https://pypi.org/project/gnss-visualizer/">PyPI</a>
    ·
    <a href="https://github.com/jopppis/gnss-visualizer/issues">Report Bug</a>
    ·
    <a href="https://github.com/jopppis/gnss-visualizer/issues">Request Feature</a>
  </p>
</div>


<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About the project</a>
      <ul>
        <li><a href="#project-status">Project status</a></li>
        <li><a href="#built-with">Built with</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting started</a>
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


## About the project

GNSS visualizer is a tool for visualizing GNSS data in an interactive environment.

![GNSS visualizer screenshot](https://github.com/jopppis/gnss-visualizer/assets/25751262/4b94577d-ca44-40c9-b3b9-71b695eca2f6)

It is designed to offer a simple interface in a web browser with ever extending plotting capabilities.

The tool is still in very early development so don't expect much just yet!


GNSS receivers collect lots of information about the satellites and the signals they observe which can help to understand the quality of the positioning solution and the behavior of the receiver. Vast amounts of this data make it sometimes difficult to take proper advantage of it. GNSS visualizer aims to make this easier by providing easy to use tool that can be used to explore the data.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Project status



[![codecov](https://codecov.io/github/jopppis/gnss-visualizer/graph/badge.svg?token=LXHBJ53VP1)](https://codecov.io/github/jopppis/gnss-visualizer)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Built with

The interface and all the plots are built using awesome [Bokeh](https://bokeh.org/) library. Bokeh gives lots of power for creating pretty plots with nice interactive features including callbacks to python code.

Parsing of ubx messages leverages [pyubx2](https://github.com/semuconsulting/pyubx2) library.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Getting started

### Prequisites
- Python 3.11 or later. Earlier versions might work but are not tested.

### Installation via pip

```sh
python -m pip install gnss-visualizer
```


<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Usage
After installing, the tool provides a command `gnss-visualizer` that can be used to launch the tool and open the UI in a web browser.


### Reading ubx files in playback mode
Analyzing an ubx file in playback mode can be done in the following way:
```sh
gnss-visualizer ~/path/to/file.ubx -w 1
```
where -w (shorthand for --default-simulate-wait-s) is used to add delay of 1 second after each UBX-NAV-PVT message. This will make files with 1 Hz navigation rate playback as if they were done in (almost) realtime.

The input file should contain UBX-NAV-PVT messages and in order to generate signal and satellite based plots also UBX-NAV-SIG messages.


For testing purposes the repository contains a file `coldstart.ubx` that can be used to test the tool. It contains data from a coldstart of a stationary receiver.

### Reading serial devices
Data can be read also from a serial device using:
```sh
gnss-visualizer /dev/ttyUSB0
```

### Details
`gnss-visualizer` command can be substituted to `bokeh serve src/gnss_visualizer --show --args INPUT` and in case the bokeh serve command needs to be modified, it can simply be used manually instead of calling `gnss-visualizer`.

<!-- _For more examples, please refer to the [Documentation](https://example.com)_ -->


<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Roadmap

- [x] Test setup
- [x] Github CICD
- [ ] Tests
- [x] Plot selection mechanism
- [x] Make plotting module with classess for different plots
- [ ] Set up whole file reading for timeseries plots
- [ ] More plots
- [x] Allow playback after reading the whole file
- [x] Configurable wait delay
- [ ] Non-ubx file support (some basic plots?)
- [ ] Even more plots
- [ ] Truth location handling (coordinates / files)
- [ ] Lots more plots
- [ ] UI for file input

See the [open issues](https://github.com/othneildrew/Best-README-Template/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue.
Don't forget to give the project a star! Thanks again!

### Setting up a local repository

1. Fork the project
2. Clone the forked project
3. Install dependencies (`pip install -r requirements.txt && pip install -r requirements-dev.txt`)
4. Install the project in editable mode (`pip install -e .`)
5. Install pre-commit (`pipx install pre-commit`)
5. Install pre-commit hooks (`pre-commit install`)

### Steps to contribute

1. Set up a local repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request


<p align="right">(<a href="#readme-top">back to top</a>)</p>


## License

Distributed under the AGPL-3.0 license. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Contact

Ville Joensuu - [Linkedin](https://www.linkedin.com/in/ville-joensuu-dev/) - jopppis@iki.fi

Project Link: [https://github.com/jopppis/gnss-visualizer](https://github.com/jopppis/gnss-visualizer)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Acknowledgments

* [Bokeh](https://bokeh.org)
* [pyubx2](https://github.com/semuconsulting/pyubx2)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/jopppis/gnss-visualizer.svg?style=for-the-badge
[contributors-url]: https://github.com/jopppis/gnss-visualizer/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/jopppis/gnss-visualizer.svg?style=for-the-badge
[forks-url]: https://github.com/jopppis/gnss-visualizer/network/members
[stars-shield]: https://img.shields.io/github/stars/jopppis/gnss-visualizer.svg?style=for-the-badge
[stars-url]: https://github.com/jopppis/gnss-visualizer/stargazers
[issues-shield]: https://img.shields.io/github/issues/jopppis/gnss-visualizer.svg?style=for-the-badge
[issues-url]: https://github.com/jopppis/gnss-visualizer/issues
[license-shield]: https://img.shields.io/github/license/jopppis/gnss-visualizer.svg?style=for-the-badge
[license-url]: https://github.com/jopppis/gnss-visualizer/blob/main/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/ville-joensuu-dev/
[product-screenshot]: https://private-user-images.githubusercontent.com/25751262/313477655-4b94577d-ca44-40c9-b3b9-71b695eca2f6.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MTA3MDAwMjAsIm5iZiI6MTcxMDY5OTcyMCwicGF0aCI6Ii8yNTc1MTI2Mi8zMTM0Nzc2NTUtNGI5NDU3N2QtY2E0NC00MGM5LWIzYjktNzFiNjk1ZWNhMmY2LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNDAzMTclMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjQwMzE3VDE4MjIwMFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTg5MTRkNWZlOTQyOWZjYTNiNTZhMTVlODZkZmQ2YjY3Zjk5YTEwMDc1NWYzNTcyYTYyNzQxNjgyN2IyMmU5M2ImWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JmFjdG9yX2lkPTAma2V5X2lkPTAmcmVwb19pZD0wIn0.QE2U4eGNuLPCiDYa2L6nfatqFRt50P7k6gOPfXFDQ68
