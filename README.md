# Dropfactory

Dropfactory is a robotic platform able to perform and record oil-in-water droplets experiments at a large scale.

![Dropfactory](media/gif/dropfactory.gif)

Dropfactory is capable of running, in total autonomy, an arbitrary droplet experiment lasting 1min30sec every 1min50sec. We routinely performed more than 350 Experiments per working day on this platform. This enabled us to explore the efficiency of exploration and optimization algorithms directly on our physicochemical system, that is directly sampling the real world.

Here is an example of droplets behaviors:

![Droplets](media/gif/droplets.gif)

## Principles

The platform is organized as a little factory, enabling to fully parallelize all required operations (mixing, droplet placing, recording, cleaning, drying). An oil-in-water experiments consist of placing small oil droplets (made from an arbitrary mixture of oils) at the surface of an aqueous medium (made from a mixture of aqueous phases), we then need to video record the droplet movements to later analyse then.

To be able to run continuously such experiments, the platform must be able to mix, sample, clean and dry both oils and aqueous phases. Previous design had to do all such step in sequence, Dropfactory does them in parrallel thanks to its design around two geneva wheel mecanisms.

![Diagram](media/diagram/dropfactory.png)

This design allows to move the oil vials and the petri dish at specialized working stations, rather than having the tools move to those containers. As a results, Dropfactory is:

- **robust**, because there is much less moving parts. Each working station can perform only its specific task at the location is was designed to work. This means less tubing moving around
- **easier to maintain**, because all working stations are clearly separated, both physically and digitally, identifying a bug or a mechanically failure is quick and fixing them is easier.
- **fast**, because while an oil mixture is prepare, a previous one is being cleaned, another three are being dried, another is sampled by a syringe to be placed on a previously filled petri dish. At the same time, another petri dish is being filled, one is being cleaned, three are drying, and one contains droplets and is being recorded under a camera.

Dropfactory enables to record 1 experiments of 1min30sec every 1min50sec, gaining a factor of 6 versus our previous sequential platform. Thanks to its robustness, the platform was consistently running for months in the lab collecting more than 30,000 droplet experiments.

## Repository Organization

A detailed README is available for all folders:

- [doc](doc) folder is the place to start, it explains the logical behind all choices done in Dropfactory and link to the corresponding files.
- [software](software) folder holds all the python code to control and send jobs to the platform
- [hardware](hardware) folder holds all the 3D files designed for Dropfactory as well as many links to source its components.
- [media](media) folder contains some useful images and video links of the platform

This repository contains only the hardware and software used to build and operate Dropfactory. It is complemented by:

- [dropfactory_exploration](https://github.com/croningp/dropfactory_exploration) for the algorithms that use the dropfactory platform as a mean to sample the real world.
- [dropfactory_analysis](https://github.com/croningp/dropfactory_analysis) for all the analysis and display of the results of our various droplets experiments and algorithms comparison.

### Author

Design and code by [Jonathan Grizou](http://jgrizou.com/) while working in the CroninGroup.

## License

[![LGPL V3](http://www.gnu.org/graphics/lgplv3-147x51.png)](http://www.gnu.org/licenses/lgpl-3.0.en.html)
