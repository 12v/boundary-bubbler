# Filling constituencies with circles

## What is this?

This project 'fills' the England, Scotland and Wales revised 2023 Westminster constituencies with circles according to the following parameters:
 - The circles' radii are multiples of 1km, with a minimum radius of 1km
 - The circles can overlap
 - A constituency can have at most 200 circles

 ## How can I use the results?

The calculated circles can be found [here](https://github.com/12v/boundary-bubbler/blob/main/output/bubbles.csv).

The percentage coverage achieved for each constituency can be found [here](https://github.com/12v/boundary-bubbler/blob/main/output/statistics.csv).

A visualisation of the circles calculated and coverage achieved for each constituency can be found [here](https://github.com/12v/boundary-bubbler/tree/main/output/JPGs).


## How well does this work?

The average coverage achieved is 86%.

Vale of Glamorgan is the constituency covered most completely:
![alt text](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Vale%20of%20Glamorgan.jpg?raw=true)

Beaconsfield has coverage closest to the average:
![alt text](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Beaconsfield.jpg?raw=true)

Excluding constituencies that have no coverage at all, Southgate and Wood Green has the smallest coverage:
![alt text](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Southgate%20and%20Wood%20Green.jpg?raw=true)

Seven constituencies are small enough and/or awkwardly-shaped enough that they can't even fit any of the smallest 1km radius circles:
 - [Bermondsey and Old Southwark](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Bermondsey%20and%20Old%20Southwark.jpg)
 - [Hackney South and Shoreditch](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Hackney%20South%20and%20Shoreditch.jpg)
 - [Hammersmith and Chiswick](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Hammersmith%20and%20Chiswick.jpg)
 - [Holborn and St Pancras](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Holborn%20and%20St%20Pancras.jpg)
 - [Islington North](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Islington%20North.jpg)
 - [Islington South and Finsbury](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Islington%20South%20and%20Finsbury.jpg)
 - [Queen's Park and Maida Vale](https://github.com/12v/boundary-bubbler/blob/main/output/JPGs/Queen's%20Park%20and%20Maida%20Vale.jpg)


 ## How can I run this myself?

  - Clone the repository
  - Change directory into the respository
  - Install the dependencies (e.g. using Anaconda)
  - Run `python generate_bubbles.py`
