Verify that you won't over-write an existing curve on the Lakeshore!

This labview vi loads the thermometer curve for sensor SN 29931 onto a LS370 under curve #10.

The 370 needs to have GPIB address 12.

The text document 29931_curve.txt has two columns. The left has units of Kelvin, the right Ohms.

29931_curve.txt was created by combining the data from file 29931.dat with 29931_DR.dat and deleting 3 overlapping points where the two curves intersect.
