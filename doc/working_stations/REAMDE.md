## Working stations

The platform is organized as a little factory, enabling to fully parallelize all required operations (mixing, droplet placing, recording, cleaning, drying). An oil-in-water experiments consist of placing small oil droplets (made from an arbitrary mixture of oils) at the surface of an aqueous medium (made from a mixture of aqueous phases), we then need to video record the droplet movements to later analyse then.

To be able to run continuously such experiments, the platform must be able to mix, sample, clean and dry both oils and aqueous phases. Previous design had to do all such step in sequence, Dropfactory does them in parallel thanks to its design around two geneva wheel mechanisms.

![Diagram](../../media/diagram/dropfactory.png)

The working station are as follow:

- [Oil filling station](oil_filling.md) prepares the correct mixture of oils in a small vial. Position 1 of the oil wheel.
- [Dish filling station](dish_cleaning.md) prepares the correct mixture of aqueous phase into the petri dish.  Position 1 of the aqueous wheel.
- [Oil stirring station](oil_stirring.md) makes sure the oil are properly mixed with magnetic stirrers. Position 3 of the oil wheel.
- [Droplet Placement](syringe.md) utilize a syringe to sample the oils and dispense them as droplet on surface of the aqueous phase of the petri dish . Droplet sampling and placement are done on position 3 of their respective wheel.
- [Dish recording](dish_recording.md) simple record using a webcam the droplet behaviour following placement. Position 4 of the aqueous wheel.
- [Oil cleaning recording](oil_cleaning.md) cleans the oil vial so it can be reused in the next round. Position 5 of the oil wheel.
- [Dish cleaning recording](dish_cleaning.md) cleans the petri dish so it can be reused in the next round. Position 5 of the aqueous wheel.
- [Drying stations](drying.md) simply blow air on the cleaned containers to ensure they are totally dry for the next run. Drying is done on position 6, 7 and 8 of each wheel.
