#
#   Filter definitions for use by icepick, irview, etc.
#
#   Based on the irlib API
#

from __future__ import print_function

import traceback
import numpy as np
from functools import partial


def agc(G):
    G.DoAutoGainControl(5e-8)
    G.DoWindowedSinc(cutoff=5.0e6, bandwidth=10.0e6, mode="highpass")
    return


## Dictionary-based definitions (incomplete)
# filter_dict = {
#    'gc': partial(GatherInstance.DoTimeGainControl, npow=1.0),
#    'gc2': partial(GatherInstance.DoTimeGainControl, npow=2.0),
#    'agc': agc,
#
#    'lowpass': partial(GatherInstance.DoWindowedSinc, cutoff=25e6,
#            bandwidth=15e6, mode='lowpass'),
#    'highpass': partial(GatherInstance.DoWindowedSinc, cutoff=5.e6,
#            bandwidth=10.e6, mode='highpass'),
#
#    }


def ApplyFilter(GatherInstance, cmd):
    if isinstance(cmd, list):
        args = [i for i in cmd[1:]]
        cmd = cmd[0]
    else:
        args = []

    try:
        if cmd == "mult":
            if len(args) >= 2:
                m = float(args[1])
            else:
                m = 2.0
            GatherInstance.MultiplyAmplitude(m)

        # Gain control
        elif cmd == "gc":
            GatherInstance.DoTimeGainControl(npow=1.0)
            GatherInstance.Dewow()
        elif cmd == "gchalve":
            GatherInstance.DoTimeGainControl(npow=0.5)
            GatherInstance.Dewow()
        elif cmd == "gc2":
            GatherInstance.DoTimeGainControl(npow=2.0)
            GatherInstance.Dewow()
        elif cmd == "agc":
            # GatherInstance.DoAutoGainControl(25e-8)
            GatherInstance.DoAutoGainControl(5e-8)
            GatherInstance.DoWindowedSinc(
                cutoff=5.0e6, bandwidth=10.0e6, mode="highpass"
            )

        # Misc
        elif cmd == "abs":
            GatherInstance.data = abs(GatherInstance.data)

        # Frequency filters
        elif cmd == "lowpass":
            GatherInstance.DoWindowedSinc(
                cutoff=25.0e6, bandwidth=5.0e6, mode="lowpass"
            )

        elif cmd == "highpass":
            GatherInstance.DoWindowedSinc(
                cutoff=25.0e6, bandwidth=5.0e6, mode="highpass"
            )

        elif cmd == "lowpass_ma":
            GatherInstance.DoMoveAvg(21, kind="blackman", mode="lowpass")

        elif cmd == "highpass_ma":
            GatherInstance.DoMoveAvg(7, kind="blackman", mode="highpass")

        elif cmd == "iir30low":
            GatherInstance.DoRecursiveFilter(20e6, 40e6, ftype="cheby1")

        elif cmd == "iir25high":
            GatherInstance.DoRecursiveFilter(30e6, 20e6, ftype="cheby1")

        elif cmd == "wiener":
            GatherInstance.DoWienerFilter(5)

        elif cmd == "lowpassb":
            GatherInstance.DoMoveAvgB(5, kind="boxcar", mode="lowpass")

        elif cmd == "dewow":
            GatherInstance.Dewow()

        elif cmd == "ringing":
            GatherInstance.RemoveRinging()

        elif cmd == "bed10":
            GatherInstance.DoWindowedSinc(
                cutoff=8.0e6, bandwidth=5.0e6, mode="highpass"
            )
            GatherInstance.DoWindowedSinc(
                cutoff=25.0e6, bandwidth=10.0e6, mode="lowpass"
            )

        elif cmd == "bed35":
            GatherInstance.DoWindowedSinc(
                cutoff=15.0e6, bandwidth=10.0e6, mode="highpass"
            )
            GatherInstance.DoWindowedSinc(
                cutoff=45.0e6, bandwidth=10.0e6, mode="lowpass"
            )

        elif cmd == "bed50":
            GatherInstance.DoWindowedSinc(
                cutoff=35.0e6, bandwidth=10.0e6, mode="highpass"
            )
            GatherInstance.DoWindowedSinc(
                cutoff=45.0e6, bandwidth=10.0e6, mode="lowpass"
            )

        elif cmd == "bed_testing":
            GatherInstance.Dewow()
            GatherInstance.DoTimeGainControl(npow=2.0)
            GatherInstance.DoWindowedSinc(
                cutoff=15.0e6, bandwidth=2.0e6, mode="highpass"
            )
            GatherInstance.DoWindowedSinc(
                cutoff=60.0e6, bandwidth=2.0e6, mode="lowpass"
            )

        elif cmd == "bed":
            GatherInstance.DoWindowedSinc(
                cutoff=20.0e6, bandwidth=10.0e6, mode="highpass"
            )
            GatherInstance.DoWindowedSinc(
                cutoff=30.0e6, bandwidth=10.0e6, mode="lowpass"
            )

        elif cmd == "eng35":
            # Englacial scatter enhancer that works better for 35 and 50 MHz
            GatherInstance.DoWindowedSinc(cutoff=30e6, bandwidth=5e6, mode="highpass")
            GatherInstance.DoWindowedSinc(cutoff=55e6, bandwidth=25e6, mode="lowpass")
            GatherInstance.data = np.abs(GatherInstance.data)

        elif cmd == "eng50":
            # Plot with high gain
            GatherInstance.Dewow()
            GatherInstance.DoRecursiveFilter(80e6, 60e6)
            GatherInstance.data = abs(GatherInstance.data)

        elif cmd == "eng_high":
            GatherInstance.DoTimeGainControl(npow=0.8)
            GatherInstance.DoRecursiveFilter(50e6, 30e6)
            GatherInstance.data = abs(GatherInstance.data)

        elif cmd == "engd":
            # Difference based englacial scatter filter. Unimpressive on its own.
            A = GatherInstance.data.copy()
            GatherInstance.DoWindowedSinc(cutoff=40e6, bandwidth=5e6, mode="highpass")
            GatherInstance.DoWindowedSinc(cutoff=100e6, bandwidth=20e6, mode="lowpass")
            B = GatherInstance.data.copy()
            GatherInstance.data = A - B
            GatherInstance.Dewow()
            r0 = A.max() - A.min()
            r = GatherInstance.data.max() - GatherInstance.data.min()
            GatherInstance.data = GatherInstance.data * (r0 / r)

        elif cmd == "engc":
            # Apply engd five times, then eng35, then MA lowpass
            for i in range(5):
                A = GatherInstance.data.copy()
                GatherInstance.DoWindowedSinc(
                    cutoff=40e6, bandwidth=5e6, mode="highpass"
                )
                GatherInstance.DoWindowedSinc(
                    cutoff=100e6, bandwidth=20e6, mode="lowpass"
                )
                B = GatherInstance.data.copy()
                GatherInstance.data = A - B
                GatherInstance.Dewow()
                r0 = A.max() - A.min()
                r = GatherInstance.data.max() - GatherInstance.data.min()
                GatherInstance.data = GatherInstance.data * (r0 / r)
            GatherInstance.DoWindowedSinc(cutoff=40e6, bandwidth=5e6, mode="highpass")
            GatherInstance.DoWindowedSinc(cutoff=100e6, bandwidth=20e6, mode="lowpass")
            GatherInstance.data = np.abs(GatherInstance.data)
            GatherInstance.DoMoveAvg(5, kind="boxcar", mode="lowpass")

        # Migration
        elif cmd == "fkmig":
            if len(args) > 0:
                t0_offset = int(round(float(args[0])))
            else:
                t0_offset = 0
            GatherInstance.MigrateFK(t0_adjust=t0_offset)

        elif cmd == "kirmig":
            print("not yet implemented")

        elif cmd == "eng10_old":
            # Englacial scatter enhancer that works well for 10 MHz data
            GatherInstance.Reset()
            GatherInstance.Dewow()
            GatherInstance.DoTimeGainControl(ncoef=2.0e6, npow=1.0)
            GatherInstance.DoWindowedSinc(40.0e6, bandwidth=4.0e6, mode="highpass")
            D_masked = np.ma.masked_where(
                GatherInstance.data == 0, np.abs(GatherInstance.data)
            )
            D_transformed = np.abs(D_masked**0.33) * np.sign(D_masked)
            D_transformed.mask = np.ma.nomask
            GatherInstance.data = D_transformed
            GatherInstance.history.append(("cubic_transformation"))
            GatherInstance.history.append(("absolute_value"))
            GatherInstance.DoMoveAvg(7, kind="blackman", mode="lowpass")

        elif cmd == "eng10_jgr":
            GatherInstance.RemoveHorizontal()
            GatherInstance.DoRecursiveFilter(25e6, 10e6)
            GatherInstance.data = abs(GatherInstance.data)

        elif cmd == "eng10":
            # Englacial scatter enhancer that works well for 10 MHz data
            # Removed reset and dewow commands - they're not always wanted
            GatherInstance.DoTimeGainControl(npow=1.0)
            GatherInstance.DoWindowedSinc(40.0e6, bandwidth=4.0e6, mode="highpass")
            D_masked = np.ma.masked_where(
                GatherInstance.data == 0, np.abs(GatherInstance.data)
            )
            D_transformed = np.abs(D_masked**0.33) * np.sign(D_masked)
            D_transformed.mask = np.ma.nomask
            GatherInstance.data = D_transformed
            GatherInstance.history.append(("cubic_transformation"))
            GatherInstance.history.append(("absolute_value"))
            GatherInstance.DoMoveAvg(7, kind="blackman", mode="lowpass")

        elif cmd == "project":
            GatherInstance.LineProjectMultiSegment(dx=5.0)

        else:
            print("Filter type '{0}' not recognized".format(cmd))

    except:
        traceback.print_exc()

    return
