"""
✅ The ONLY file you need to change to swap algorithms or network architecture.
Both train.py and agent.py import from here — change once, sync everywhere.
"""

from stable_baselines3 import PPO
import numpy as np
import base64
import zlib
import heapq
from collections import defaultdict

# ═══ Option D Hierarchical Configuration ═════════════════════════
ALGORITHM     = PPO           # SB3 algorithm class
POLICY        = "MlpPolicy"   # Use MLP policy on top of strategic features
POLICY_KWARGS = dict(          # Smaller architecture for macro-actions
    net_arch=dict(pi=[128, 128], vf=[128, 128])
)
SAVE_PATH     = "model"        # SB3 appends .zip
# ══════════════════════════════════════════════════════════════════

# Pre-built base64 encoded compressed graphs for Ms. Pacman Mazes 1-4
MAZE_1_BASE64 = (
    "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"
)

MAZE_2_BASE64 = (
    "eJwleodbFMnz/vO86516ZzgHE010yY0CjrmBQUdFHTAACiNJGXCNtLnVVcREIygLBlYF6ft+cvon"
    "f1X8rp6+fevkZLanu+p9q2pHgJ3B9mBngMJgR1AYpESrIO8EcBLHaaEdJ2jhFOF7wF3cJ8MDwg+A"
    "h4SvAlcwQoaEcAa4jmu0cIPwDfZuQqWhdqkKVUFIVapKEK6qsai11bbWos7WWFEMUSRKRAlEsSgV"
    "pSBc1gYEOEqGY2iD2ga1XW1V26F2qG1qB3s7gwRtSWvSliBIjpLhGGH7A/a7XbJLsD/ssl2G/WmX"
    "+lwqXoldr4tdqs/FK5fdS4FJMSEmBV6Jl+IVe6+FLYMtt6W2HHaXLftbgL8Hfw3+HuAfwd+C3HPk"
    "XuSyuRfIPc9NNAF70UgLPppgBWzRlLBFKVtMH8IWk29LOgU6xFkynBOdwryEmTCTZhLmpXllXsG8"
    "NpOqCrQp1a8F3tBDmPsw98wD8wDmvnloHoLwo1KgDCW0UIpyHHVoc8fIELqjLkaqD3HqMq1UvCYG"
    "gTWIf4lTA1kMZvuzg1kMZIeydg/sbttgG2D32EZzE+aWuWFuwdw2N81t9u5EjYgaoqaoCVFjtDfa"
    "m4qazviR/88A/wr+EfwrwD+Df5PhP4TPAedxlhYu4BzUW6g36p16R0hNqSkoS55OHdFqXN1Vd6Hu"
    "Ke2tg7feW+uth/ebt877jb3fbSPooZosbeBe2+i64bpcj+uBu+i67QnY4/akPQl7wrbbdhA+1QI0"
    "o5WMjkYLvSN+W2mb5rdVYStAuDJTi0xNpi5Th0xtRmYkCNerb1DfVV59h/qmfqgf7C1tDFIbgv8F"
    "m8iwOdgYbA7wB+H4HeK38VQ8hdjG72KLeDqe8jQKtDdeoFNb6cPT7hvcd5d33+F+uG/uB3tL9grs"
    "sL1qr8JesSOfA3wKvpDha/A5+BpgkfCwjyv+kH/Fx1V/2L/qY4TwLiBNbzYNVGAXCoCt8GhhG+Ft"
    "wHbChRo7tSBDkS7UZifMDlNoClNPhNlphBEpU0SwsBz0F5ThbpS6F+lId9yLcD+6G43wr0vIMOqP"
    "+F5bqiDwAu+odxRem3fMOwYvJO8qvCveiDcC76qXeAm8UW9EW9y14/auhbb3rJqEeqleqVdQr9Wk"
    "es3v/VW9gBS7ybBH1Is9Ag2E3wq8E2/EO4EpwrYbtsd22R7Yi7bbXmTv0jONrH6qsxrP9HNtO2Aj"
    "22k7Yc/aDnsW9pztDB2O00nPVCJTkanKVCFTnanMVPMLrqrQqNRpXalRpSt0lUY1YdkEuVc2yr2Q"
    "vmySPnv7tvNO7iDDTtrL4QRXkqHkCsWrZDi5yt5I8gR4CkMLz/AEvsY+vVfv09ivfV2iUaqLdalG"
    "iS4jQzlhWQpZIstkGWS5LJXlkLtkmUpBQa1Ra6B+USn1C9Svak1tgJqgjiwlW2VQG8hV0FYXmCaY"
    "RrPX7E0Z3zQ99o0P+tfevzr8zf3F/c3h7+6vbipK2TM2ehfZM6mpyJ620RAwiGEyCrxDtCjsDtOW"
    "0+Y3kqFJNAiThtllKkwFTNpUmkoQrhKNoD9qEk0Qe0WjKUqZYjoxwhTDFJkSUwJTbEonNF7ol2SY"
    "1BN6UuMV4UqHKlfhqhyqXaWrdqghfMXhqht2Vx1GCI+wlzh1G+qWuqPuQN1W4zVANWrJUIca6MvQ"
    "/TrW/YT0gB5gb/AmcIvyxCWHXrrzvQ597pKzlaDbXGWrQBmiMvcMuacUdrMcdp9tFdgmCsQ2ge1i"
    "q1Bv+CC+VQ1Qe1SjaoRqUE1pg/Tj9JP0E6RN+mmnjw7/LBnO+Z1++hnS2fTTdBbp5+ln6efsvVAJ"
    "mhM12pygJVGJvgR9UffqXuhLum8pwHLwI1gO8DNYCn6ytxK4Ybgh+tZX4Fb3AI73oA+r6SWG63OX"
    "3WW4fvJuwd12N91tuDvu1l0f2r9Hhvv+Xf9IBBUdjlSE5uhIlBHIFF0TmSJkijMiU0xepqSSI0IV"
    "GW1kJQYSDCb9yWCCoWSAjjB5w8lPixXKcisWP62zDREaoz0UwNFEwXzJYZnC07LDT7fkfrK34rzj"
    "fNtPeCfgHfdOeidBuD33GDmTe5QzyD3OPck9Ye+pmoF6r2bVLNSM+qA+QH1Us1eyGM5eJcNI9kpW"
    "J6m7iR4ZT+4mKT1yL9GJ9xXeF2/RW4SX9756eXjfvMW0TlXo9N1desHhk5t3nxw+uwX3mb0vbidQ"
    "SLfTfQH9l6/uKyG36BZBOB8eR3giDMMTCI+HJ8OT7LW7a3AZN+YycNfcdXedvRvyGGQoj8oQ8rg8"
    "Jo+zdyJqAG/HXIBc8DHIBZgP5oJ7Fvcpot1LcDe5nzwRa+gCFBrxVNgc7Jydt/OwObtgF2A/2fmw"
    "G2FX2BP2ILwYdoenELaHp8PTCM+Ep8IzCKPwdJRFRzZ6Hj1H9CLKyjuQt+W4HE/Va3lHaqkJ1Gk5"
    "3uGjkzJqvB3xtnhHvAPx9nhnvBOEC5v5MLREZQHKg9KgPMCuoCzYFSBN2M3D5Wi7FrC6dZ94mxbk"
    "bchb8s45H+fpcJ/3ccE/58vTkKfkGXkG8rSMZJSSZ+oj2XHa4ow9RXEEFD+meoCL6KaFS+iha0QX"
    "agcZdortQlIsL6oXsohCuiyWxeTJkngT4o3x5ngz4j/iTfEfiLfEmz9rfNGf9BeNz/orGRYJh0nq"
    "WBKOHE+OJ6kTBMLkRIKT5K1oOP1TO40V7cbdH3Bb3Ga3Bc5zfziPvYKwDWEQHg2PImwLj4XHQDi8"
    "6eOGf4sMt/2bvkd5cZtX4G2Dt93b6m1nb4d5BvPUZE0W5rl5lnuF3OvcZO41cm9yr3Jv2Hvr1sGt"
    "devderh17jf3G9zvbr1oAZHdZtGaKgxEIFoEk9/CoCiY58OyEEwIvCBiWB9hN+1k7inoXjwrClBM"
    "P10coIR+soS90uCCjy56A138Drr9VofAtbiAaVqra3NE2AL3NsK76A2FcUxFbwngbfQ66nQ46zrc"
    "WYdzrtOdczhPWJ+APq5P6pPQJ3S7bgfhU+4G6JzfdDfhbrhb/T4G/Mv+gI9Bv9+XrSnZIim/mPcw"
    "02bGzMC8N7NmFoQ/XLe4YTNTNyxu2uu2N0FfcinpSxAnvUmc4DLhWY0PekZ/0JjVH8kwRzgqSkXF"
    "HSISHSLVSR9RUe4Rx4aH5heYX80a8yvML2atWcveuk8BPtOWJQ6jFApHHcYoGcjPkJ/kF/kF8rP8"
    "Kr+C8OIrziyvyfBGv9JvNN4S/geTy78Huocjb7e+yJG3pxqUNIgc25SabrZqqtkSbrGuHe6kO+VO"
    "wbW705kKZNKZSh1zUumTVZDVslJWQ9bIKlnDXm1mCtdt5t2ywJL4SYYVsSxWBBxh7yK8Hu+Sdwne"
    "Ra/X6wXhvsoAVUFFUBWgMqgOTB7mm1k032C+m7z5zt4P3ZEidtV5lxZ0hz6rz0Kf053XfGT8MT/j"
    "pzJ7r/vX/H84/NP93f3T4V/uH+5f7P3byRLQzSq1M7Dv7aydhf1gZ+wH2I921uuEd9br8M7CO+d1"
    "eufYO28aYRpMk1qGWlI/1U+oFbU87WDdezLMuGk34zBLOP0UlPee7XDY6ba7nQ6FboeLs6n4+eVs"
    "XzZ+jjgbv2jhbNea/I/J73+J9aanUmlKt+l3aZtKT1UQkw4PINwfHgwPIjwQHgoPITwcHszvRn5P"
    "vj6/B/mG/O4fFkurIgurEouTz5INFcIjYXPYjFCFLWELwtawWZ6HPCcvyAuQ52WX7ALh7pMJ2ik0"
    "tCc4lZxMMgmuJ9eS6wluEC5hmVNMqoq01T6YRzCPSQk9hjHm0WUHTqr9DgOUYi/66PEvkaHXv+jL"
    "esjdUsrdkPVyj9zDXsOAwKDoF4MCQ2JAyFMcF9u9O/BuE4kfTxGlv+PpzDtk3mamMg3I7Mk0ZhqR"
    "acg0ZZqQ2Ztp3M9U8IDucuh2F1y3Qw9JlGKLEpZ3FsWkFUstygir91DTasbo1BNtxs3dJxpPtdH5"
    "g8gfyB/KH0L+cP5g/jDyR/KHZh0+0Ev74PDRzTqvD15Mxy+Gd9nr8y6z1x9eQXg1HA6vIrxCgXRk"
    "DQXWqyGFUgEUUb4sAm2SwG3gDlGoO8A44VO8r6fJcCY5lcw55NxHSh2Yd3NOrWU6uk6tg1qr1scb"
    "EW+IN4XD/NcPqQIoj8T1VqgCtW0ywqvoZfQqwutoMhJlEOUkysshdokysYu9dNphF1HCCodKl3Zh"
    "H8LeMA5jhJfDvvAywv4wlpcgL8pe2Qt5SfbJPshY9i5q5ClZXEaqHzFp1n5ggDTrIx8P/cdkRIUf"
    "EQeOyhCVRuVROaKyaFe0C1E6Kv8u8EN8Ez/4In8X4/zFNV076PN0Ac/zBbygL7DX5Szc9Ir1CuEJ"
    "b6cnUCC8QjkMeUUOySuQw/LqN+A78rTwA98Qv0D8PJ6IJwjFL+OXIDwplyF/yiX5E3JFLh/3Efon"
    "yHDSP+6f9NFO+EaCm3Ru/86U/R9OTkNa+V6+h5yWM3IGhGfFPghf7Bf7IfaJA+IACB/cprFdb9Xb"
    "NbbpHVrsASmmBtEAUk+NUyL1TtDpEgUWW61nt1psswX2EyfaBZ1kMZodyY5mMZZNsqIKolpUimqI"
    "GlElatirvcT5vZcMfZThoz0s63c/9GmTH/jeWni/eutmgFm8p4UPmKFF6CPUJ6jPakF9hvqiPtm9"
    "sD5J84hlxxnbcSGLruz5bFcW3dkL2agYUUlUFJUgKo5Kn7KEe6KFRZEtpEenayGsugd1n+T/fZb/"
    "D3SU0md0x91oa4BtQUGwLcDWYDsZdhAOD3PkOBQe4VCjHiR4SMTsYYJHyYMkfoP4NQnyt4jfxO/u"
    "J3iQ3EsOAQdxmAxHcIgW6a7DmAcWkKOFT4QLWe4JkrTwhr2rylHYbHbN9EHJeb/A6ssQOEivI3+E"
    "76bKK76bzfYUSGa129Ogr33qpgNlXDIwjd8H7KfI9JxVUlY3CZCSIjVFossX1mLa2ulpC0uB/b3F"
    "jJ22P/iYLZFhmQ5aHSBJDi0GyAdfg3yQ+hYsBvnW0gBlxCUyDqtsln9jxp13uECc4AKzgi7nzcB7"
    "7816s/A+eDPnE5xLLpChKzmf9PmI/V4/9nHZ7yNeQF6/P8CRcpAMQ26AxAqGCavfoH5X69XvUBvU"
    "b/Y96Aln4jnEH+NcnEM8F8/H8yC84PMG7RX3He65B2R46O67hw6PCA8y/RjyzS5Wl+U9AhdFt7go"
    "0CMuiQQYxQgtjCGh4EZhbs49tHhkH9hHFg/tYzIYwp8tPtkvZPhK+KvFIuFjSYpJ49FE1ULVqDpV"
    "B1WrpJIgXG9WUo+dceancSBAnBJ3KeypX1lur1W7uL5YPiQwTPF+WOCKGBJmAeaTmTefYD6bBfkJ"
    "ckF+PqBxUO/X4hDEYXFQHIY4JI6II+wpOQo5JhM5Bjkqr8lr7GXGgGv0nSI/1eGf8aO9j4DHeEgr"
    "ZWBSlKGQovyUegLlo9lXe5v9lPJbCLT4aPWb/bzDN1I03xzy7jsZuGQ0nMWV7FBWLkH+kMvRbhYq"
    "9W4Dc9ONbiPcBrfJbQLhzfow9CF9RB+BPqyVViDc/JzpaVa8EJgQz4Wthq0hyVyD1aJqLXt16hnU"
    "U5VVWajn6pl6DvVCZc0HmI9EDz/CzJkPqgmkm/eqvfTA9ORNYcg669gKQJqRFlxqBZ3AWXTQInQO"
    "thSU7crqLAW7WivpY7rOFjoIIhx5i2920X6z+G7z9k6C8eR2Mp7gDglDe4mLP722F/aS7XsS4Wlk"
    "oqcRnkVPomfsZSOrYI/YZtsMy1SvBbaVvP2w++wBewB2vz1oD8IesgfUNBcZ39sLsOdtl+2CvWC7"
    "vQJ4nrc1pnj+Pc7H3xF/i3/EP9hb6ua70kOGi0l3cjHBJcJn/NRpep2Rb3dzXbRePYYy6pEyUI/V"
    "E/WEvacnHE6648Q50e5OuLN89TqTcwnOJ2eT2w4k651agJpXn7x2eKdIUp+Cd9pr38rBvUB/BOYo"
    "ws6BItNHWoRIXg5zhXDI/Abzu1lvfof5zWwwG9jbaNYws06Zcq7hlFnieSvTLrOXmGWmqZ8Z+0DS"
    "kaAziegxcJawlMx46sxrmDfmlXnDZeW3D/iy3beqHmo3XaDdXCCpfwO8xWtaeIN3ZJgi7DaDTtof"
    "tjVlg+nAtuzgSuN2bRpg9pjGlQAu+Bm4IOXa/gxWgtxL5CZIX00i9zL3qpprW1XBhiDFTPJ/xCdT"
    "/wm4ptrj4yJpITUGdU2NqmtQGTWmMuxdX+C66HywW6Ne7yFDg96tGzQaCY9xhfKarygbzakP8jDk"
    "IXlEHoE8TEFAgXDzioNzP51zKbfyp1txJscned7Mw+TMwrif0r7ed4cWg/3jvjsKt1owhzvqQheC"
    "XuaxqIIpRWVUiagiqppnorTgzEbQW9i0yyHtyl2Bw1aSp1sdthFWOX6ieTUPlVMLYwLXxKi4JjAm"
    "MuJbkMoH3ymQb3agnSQDq1t1i6tgN+0+TqT7pzTeaUuWmtZT2o73MKO86P4a4C/B3wLZBhnIo/Io"
    "ZJs8VsFMPG0ryVBF3DxeAh3k5XgZ8c94KVPDZdDaeoCoLi3sQT0dfHhbvIKzWZzLdmbPZXE+ezar"
    "VijbqZ/eeZYTF7wL8M57XV4XvG7vQr4a+Zp8Vb4G+dp8db6WvbqRLJLs1WzOpubtnM1NzVtwIaQZ"
    "aKEMa2+ANORNexP2lr1hb8Hetje903zoz3hn+NBHfoS90T4y7Ce8P8IBwuF5hOfCC+EFhOfDrrAL"
    "hLs9l/JWSPa7P/mE/R8ZbcSfgTzLcqFTnoM8S4LhJhc5bshbkDflbbmLi63pKcDS4W3lpk9LEjl0"
    "uDMkoxGRiI43IP493uhZeNMF1puGZylvvifPm2lxaCUCYH/SjbLL3hDzgkFvmIveQ6GfCvcd94/5"
    "f/Lp+j8y/MX96c7zdl7I2s9cCaJkhdVU9RWEF8MhhIPh8JxGjkRzTqfmdO7uvM5kkXl+LZt5jkw2"
    "8yLzgrzMhMyAksl1eR0yI0mL08WbJiMKRsnwCUubp+YpIfNMFUMVqRJVAlWsSlUpCJfF6xCvjdfH"
    "6xH/Fq+Lf+PvuF6HXCg4po9zoSDUR6HbyDsGfVSH5g53dsbbLI7awB61OGbbrCsEhWjhWAG7wj8C"
    "bAk2B1sCeMEfgRektgReW0Fw28cd/5Z/hwsu4/4n4DPxqSEfw/6gbxI8TsyoGU2ZMQKJGYO5Zkbd"
    "VtBr3Oa2gUTnVrcdJDq3yW+Qefldfof8RvntBwgvvQexzWnk3iH3NjeVm6LDlXvXzSquy1fVnPGr"
    "+kC6oBeuA47fZye4QPKA5cF9Xz3iuPzQTBGBMO+MTZnpx9ZMmWn235/nJtsFMnSJ86JLoJuwWYZZ"
    "IsLwE2bFLOsukEbo1t3QXbpH1DJrrhN1ELVCCgnC9eYrzBeS+4swX00+tDhuj9njFqE9QYaThL1u"
    "Lhp0eT18jy7q0yBie0qfgT6toxGBRFwVJNJGKD6McnxIxF8C/JXO94zF7KrkJ2b4wR4DQhylBA3K"
    "NM/iaW42vR930O6O0w7j7i4ZsS/tJoFXeEmLQvckwn2kQ0ie7ycUHrAr3N10sg6yVsp5jQU6iQsa"
    "n/S81qf4kdoPCayyHIEjxHO8D/A+EpH8yERyriOLzmyUfRjhUfQgehThcfQwehzBEFZLUD/UsjcI"
    "b8AbqtWo0zW6TqNWSy25pF+P/D7k/fz+/H5CJHIPgPDB6SBFaTt4H9xwuEls9gDHgoORTJhRjcgT"
    "XJ49KU9CnpDtsp3rlSfDQYQD4ZDsh7wsB+QAZL8clIMgPGTGYe4Y3c99zMvZMwkikrcRC9yOZIBb"
    "If20MEQy0rsF7yYJ+9uESNaPwhvzEm+M21jXvGvsZU77OOOf8u8C90g7mhTTNpg14UWEl8Ke8BKX"
    "eHvDXvb6lgSWSWwKn/sl+26x0rtNRlzmViLqWbFJsZsVW/1xbsWecLkHyN3PPcw9RO5B7pEHEB1J"
    "yRHIqzJRG5lyb1KboDaqzWoz1B9qk6iASJN6q4SoEFWHNA7rg8TwcITY3jUKI9mxrB6EHtBDej80"
    "lyEOgHjrwUKREkU7Bf1TlBLFhfR5UOMQ/XGhhbA7bTtr1FNkOO23+5eziLP92fg99zFn4hnE7+NZ"
    "oUCUt1k0QyjRslOgUOwQz7gJliXDczyjhReE7zncp5OYfsEdk4nvGj/0N/1DY0l/p3iH3L2czt3j"
    "L35X7GWl23RJoJfkQK9AHwmCPvZikX6A9P30w/RDpB+lH6QfcYfmoe0D8UE697CXbd8pHjY4TYYz"
    "oJPbDKK6LboFulU3RzWIaqPqqBZRTVQX1bEndR90r47tOe4YnrfnuWN44anAM/FEPBPIiqeiyqKa"
    "kmg1p9Eaexw4QZduh8VOu532iVChjT8j/hR/ib8g/hx/jb+C8OK0Tr2nHG11MTf9ivR9Hw/8e/4i"
    "kMdXWljkosEWrod7phqmxlSZGphaU21q2as7adG+2ramiHGKDKwo5UGmMwfkIciD8nDe51uzd6dG"
    "od6h47WIf43XjfoY8xP/vca0ntHeT3gr3rK3Au+n5/IlyBfnS/OlyJfky/JlIFwu8xxgF//i8FdK"
    "WldY/Fwlo/Bzhd5xqpm0sUrJHOScnJfzLH9ycoHrsvPnBM6Ls2IkQZJcTZIEo8lIYut5TkCql1AT"
    "avJ7gB/Bt+BHgCXiN0JAFBWKfQL76T0vsH6bp7SIz8QQ4k+8fQtqD9PNBrnClRMnHeqcXClxKHal"
    "ZChzJa7MoZxwvU7t1nJc6qiUKwll9gjsYavUHDeZco0aTUQJmzT26kZtfR4P2GdLYIttafot0m/S"
    "79LvQBzp7WiCMXr4sQTXktGkJkBtUB1YCVtn679zdfKbdZROLrm+TAl31kozpciUZMoORThMUelw"
    "hEPRkShfhXxlvtqd4axz2kVYZRSjcIkbc2PcZRrNc4fjGxm+67y2H7lsO2dHYcdsYsdgr9lRe429"
    "jD0KyrbHKMLbkHJvyGMMx8x65vjr3HFQpAijCe4UvYxeIpqIJu1h1jRHLvBQRRcZukG65jvo2X98"
    "sPhIKeOjxdzqL6SU+dHaOa4W59QGlvMb9/Jm+fqOxW06suPcqb9jTSlMiSkzZTClptzeZsp2x95h"
    "yjZuOM4/idodTq2W0nHatTvzB8wWs9lsgfnDeMZjryDk2ZvjGOPKxCjtAla7bq+QeZ2ZzLxG5lXm"
    "TeYNe2/NOpi1Zr3shuyRXfEKD9m4+KeZY7WZUyKlio4IVaiKmNeICq6tpwNzA+a6uSlruV5fd4m1"
    "WW/yGfiCTzgocEgcEFE1X/mq8CxTyM7wHFPIs3STaWtPeL/C+8Vbq/I81LG4jfn6djIQ/XByFvKD"
    "nFE3oK6rm+om96VvmCWYH2a5nIuXZa4CqEQa5jOXCL6YL1wi+CrT3MmvcCewqvlO8utqbwAaiWU3"
    "Ag1owltm8m/0O40p/VZ7O7gZtdMUgHZtq9kKU2C2mW0w281W2wamX14K3hri52v4cVPqC5fZvqqv"
    "XGZbfB9ghmTXTIBZSpmyh2um3fIi7+Ilm+Fjdd1eBx2qG2E/V1cHwgGurg5GbxC9jt5Gb7HaVnoH"
    "wlNHfbQRhz3Gpcqjfr4ZeZVvydQjszsjM7u5ul3/nwD/Df4dBEAbWuHOw61WmQi5LtfFXrf9xvNT"
    "ea+fy9EDHiXWfm8wv5dTfdMt4DZu4rJAP0X1fkFoQJjNfGY2nebzdIYMfIc+BPgYzAYfA3wI5gJ5"
    "mcu//W4a7r2zmQkQNX6ZeYnMRGbyBTBB2WYCRHJeYBn4iSVahFbwRuCteC28z/A+eV+8L/A+e1+9"
    "OeYwOS8Hb86bd5+5X/wpXw4Kirvyu5BP58vNXZ6j0uYez1HdvZygP4kTd5rv9SlzHSZjbuyySNty"
    "4vREcb/SvuGoH/jLnNh+kmFFL2szAfPCvEzfQ/oupa/7SN9LPzA/uBO0FG/lLm5BvI27uFuN4TbF"
    "EznExeVBVc4Tb2XxrzyJtVaTJN13l9h0PIv4A6XgD1xwm40/sjenxqHuKKKk6KGr78axyv/eY7Wr"
    "M8PbNettgPe7t9HbCG+Dt8nbBG+zt1Ec5LLVgTNARDnzNUv6V/A64EVe5yOujz10j12KWK975NQL"
    "rgBN6INcRzqgD3Ed6eALjQn9XOfucw5/YC/D9ttYcM+oyIXtCE+GpwqC1FYeFGqLFzhJzocBt3Ta"
    "ZAVkWlbKFshW2bwfOIB9tHAQ+2nhEGG5H3IfpboDnOr2746wJ6qP9nArtSHyvvFowHfvO48G/PBu"
    "MGu77t1k1nZjiKcLBrPFDiX0GBtdapPb4P7nNjlsJs/UcY6VYSfCjvCsXGSJ8fVYhDA6GoVRKjwT"
    "dhyL5A0Wi9fzlchX5KvkPp4E2h8XIt4Z05FNXSZKEhd+cfjqPjvdCh3oljvMt2+7l3wQJ5GN8Dx6"
    "Fj2P8CLKRtu4Cr+djNjCNpJ+lPopUrzlWss7846QmbLjpOkpuuojTLWVWOSaZt42sRbmUTr4UVP0"
    "kMcmHyFeBLGMvPc7j8FtUIugSJCPXyN+Fb95EWGCfm3EDKiD6CZuJTeSx0nqEWut0agKUWVUnebR"
    "gIogn+avtytfwce9MuzgOYRO2QzZIlUHF+oixAWIvXjrFgdusuebkG/M783Xsd6nfUO+Ll+fJw4v"
    "87vjPJfKFv/t8B/3L6f+gNqiNhdpFGuhZ/kCzwRfHRZXxzKQd19dJEE0rF4HzM7ablvcofRi68AF"
    "wTHuUFzL2lUZ0DYdqFGoRI1NRHi5mvPoO05G3Vwu7hLqAfcIHqqHUA/Uo2tcNc5Qsub5v96LDpdc"
    "j1NbmCt7yuOHKjDbefBtm9nB8XWnO4vVxvk5Dl9nzSaYjWZzvgX55nyr2smDooWqEGqnElE9Ihnt"
    "jl9xL2EyyyTxuXD9cNxH/JWnA35xa+F+detyEzzl+dK1wQXuqBvhEZ/E2wzvD7p6f/DV25J+g/Tr"
    "9Fu7CMvvOc+JenFJY5l4cbnGLl2md/GUWFp7GZD2uO5dh5fxbpg9MLtNg+1nvjtgB/jGDZoqmEpT"
    "3RKhNWqO9nCK2Y3X3IF7E3k/QPdkyVsC3ZNl85yjUda84EGHCXMNZoziWIY1+HXZARnJTtnJZZMO"
    "b4HD5bz3Cd6C99lImDpTb+r5t8v4F8Rr4l+LuYtYAm8LfzGv1Ufgt/gu4Umm0djjCY8COwh6yiE7"
    "xEONg/ID5Ec5Kz9yXp2Tc+zl1HUu7N3wdsLb4RV2JehOLiR6hGeCruqkQMATW0WmHJldmbLMLmTK"
    "M+lMmr0KL4J3xuuw07DWvje7udhY74U8k3Qs/ol4JV6+4eOmf90f5hbGFdfro8+/5MtGyAbZVMvU"
    "ssbVOUhX6+wI7FWb6CugXzusr0Jf0SPxJF+ql9U8H1ijb/IcxC0yIkk3bfSCidfzfAP3tBvzjdzT"
    "bgpbeQClxd3hka3xY6z5j1pvmbn3kk1gR+xovjWVJ0Kcb/mPw3/dv91/Xeo/qwGqhnVxtVbrodap"
    "3/QQ9CA9yDA/yND/+Gc3urzAN5EvyhcxixdFTIqFcwM8JjboBvkkDqUfszwy7iIT1h7ZALlHNrZF"
    "OBoFFOHQFlF0u8pdzJGAM32rbz9xRWoh/p0LQxu6s+jJdmV7sriY7c5eZO9S1q2BS9Hp/oVP95r0"
    "S6Qn0xPpSaRfpV+mX7H32g2BHmHYFfA4ztbrPHKT8XNveYLmnfcLc5dfZ3g45L1WE9xDeNnHkrI3"
    "G00henfGuhU4534eYf2qtNvBZaCd9hDz+YMizV3jiijNdVY6BHwESr8JfBd5kdnDxKThvsUDe8+6"
    "ZazOqP2EW3HLG/7/nv1wWHLfXZkFD2XX8ABirXOzWO2df4CbdR8vZdFL3/Ua64BMomq4YVTtUnBw"
    "a3qz6KMtuB/hXvQgSk8g/SL9spzb9bts+jVvwZsHER5G96PoFdOpyeg106lXbifXsAojnt6OitJ3"
    "Oe9rVQZVqsrdEk/8LsuYaxV9LRbcomi1CGyLbY0QRC30suhVtUbRJLiL/oirZg+TzFsQWX7nPsLN"
    "0cPP8UjXR1kJWSGrMpNMpV8G/Je12YOsSQ5ELg/uGXnzfIlzLsf/33y+mMVfUScPnJ3N6jZOX0fd"
    "79wt+u3/AZBhpGc="
)

MAZE_3_BASE64 = (
    "eJwlewdbFUuw7fetMR/dagMKY26MY24wtXmbGyQqbElCi4NxzK2OskGBIQ8gOfVN791737t/8lX7"
    "Tn0jqzyHvWd6uqrWqq6zEmM1Xo5XY8/+sPFKPONj1p/2Z33M+TP+nPPm/UfAY9TThUdoIEMj4UM+"
    "DvsH/cM+oSP+mRhn49Px2RgiPhOLGGWE24Gn6CCDRjskhzwgS2UpIXlQHgThQ5MCU2JCTAn8EZPi"
    "j/OmxX4fB/x9/gHf47v2+9wv0yjXQpdrnNNluiOGjttjHeNZ3BE/i9FJWBZB7pCFcgfkTlkkdzqv"
    "mLeCt/EW3gb+lLfyp85rX46xRA96KMbh+GB8OMah+Eh8TeO6vqqva1zTN8hwk3CjRc422JxFo31i"
    "c0eRO5I7ljuG3NFckAtA+HiLRatttq0WbbbFtjnvqT0mEIijIhDecRGUHRPXE9xIriU3EtxMric3"
    "E2QJnwHO4jRdEDiDyhgV8UMyVMWVscnDdJse0wOTN72mF+aX6ZFvId/ISEaQb+U7+Q7yvYzMAsy8"
    "WTSLMAtmSR4CLezh9xl8yLzLfMjgY+Z95qPzPmXMB5j35qP5CPPBfDKfQPjzXmAf9tCFvdgP3gn+"
    "jD/nzwnxkIcg3FUUY0dcGO+IURTvjOMY3+MfZPhJ+GeMbsLNMVriprglRnPcGpuXMK/MC/MK5rV5"
    "aV477400kF/kV/kV0shvczHm49l4PsZCPBdXAdV4SBdqUAXZB/lb9st+QnJADngyuZzIfv4W/A2P"
    "eAT+jr/9JvBdfBXfBWLxTezV2Kf36H0ae/V+rf6B2qw2qc1Q/6gtaovzMmwD2Ea2nm0E28Q2sE3O"
    "+8fWwdbaelsP+8jW8TnweT7L58Hn+AJfcN6i/OHJn5diGcufkD9kt+yG/CnzyW0kt5I7yR0kt5O7"
    "yV0QvifnIRfknFyAnJeLctF5S2kD0sdpY9qItCHNpTmkT9LG2OKH/U4Bh582tvaHZ3+uxoR+wnbT"
    "33bD/rR5PutuZMbOwy7YObsAu2jn7aLzlnYJ7Ba+2C2wR+wSe5y3V5y3uGDP2QsWF+152ybwVLSK"
    "pwLtok20C3QQPgBw96KBUhxAAbxCMDD6E0XkFQE7UIhY44f+rn9oQj91sA7B2mB9sB7BumBDsAHB"
    "xmD9YIwkHiLDcDwY/4fG/9L/rv+Xxv/W/6H/t8Z/EubL4Ct8ia+Ar/Jlvuo8y613wPLVUqsGoYZU"
    "ooagBtWwGnbeCG93cdrBO7wDmrdzzbXHnxHsCDci3BRuCDch/CfcGP7jvM37QY+wjx6LHpCSg8Az"
    "0SHYdbBr7Aa7AXad3WQ3wbLktYM9ZR2sA6ydaaa9Ar1ds44owbvkbfIuQZS8T/gU+CT/w/+AT/Fp"
    "2QOZl72yF/KX7JG/3J7sPaDXUHx0cNpkBRqF9EmFGkWEizR2EL4ocElcEJeEJ8VFIc9K4V0mT579"
    "qdFN65l2In2ePkufI+1MwzR0Xtd+jQO0deVWyG0yI7dBbpdb+y367AAZEttv1Ruo1+qtegv1RkXZ"
    "emQfZeuyj5B9nK03JTDFxjc+zC5TsiKwKpbFqvBs2Yqwosyl43IynIvLYjULNaPm1BzUrJpX81AL"
    "am6He/c7yVBMb79N46lu1U8pX+s23e68Dn3Ex1HK86oLKlQv1AuoLvVSvQThV1+BbzB04Tu+YjrG"
    "n3iGDLPxdDwCjGKYLoxgDF8y3ueMyZitJuN9yZgtZqv0vEuQkGvkGsi10pNrIdfJNeYMzGlz1pz1"
    "jDBnvggjvK+CfpxtEGgUj0WjQE40iJzwcmefkHckxlHK40djHKNMfixGQLjbIu+iyKLb9tiXGbzK"
    "vMi8yuBl5jUZ3hDe4V7eTjIU6x06fI/wXfgh/IDwffixW3v5jjxt/7xGvqNb30twnwL9foIHyb3k"
    "gfNUckjgsDgoDgscEkdEUoRkR1KY7EBSlOxMdjqvOH2N9FX6Jn2D9HX6Nn0LwhHrAetledYL1sN+"
    "sV/O+50eQMrT/SlHeiAtTUudd9DmXUbosT2gJ+m1vbC/bA+vBq/iNbwGvJrX8lrwOl6TxBiMB+L9"
    "AvvEATJwsV/8dE//w8qTkCfkKXkK8qQ8LU+D8JmnFu1UsNotOqhkdThP2yPAYRwlwzEcQfQEUVOU"
    "i5oIRc1Rs/NaxhRG1TgZUjWmUvpRMa7SeqSP0rr0kUt29elj5zWkk0in0ol0CumfdPKxRQOl2QZX"
    "TB/bzxnaD58yvyx67W8y2u6/bJ9FP+FCH0V+gV/kY4df6MvfLgT7Ypfxf5Dhp4jFT4FuwmkF3URa"
    "mVbSTaQP04dIq9LK/3Rp6L90pUCFeEiGKlEp+HePxwdi/o3Ha/iPUge/8x/gMf9pfsL8oHLbDfPT"
    "5KX2LutLWj67rHFFS33WQtgzVlictWU2eozoUdQQNSB6HDXaAVB0JjaBHaRYHYQdIq8N1pGAp7B/"
    "1xe0tk9PW5yxp+hz6FNOW/4Y/BFv4A3gj3kjbwTP8QbbiL9cIwfr2MYT2Cab4x/A3/OP/CP4B/6J"
    "fwL/zD++E14korL34r3AB/FOHHTZ/BAZvbuDsGWeLV+l2LflhKkenIMtt+ebNVp0k27RaNXNFOHk"
    "tem8Qr6iR+UrvLzKV/aobIPLKY3ZRmQbsrlTCqfVSXVa4Yw6pcLXCF+Fb8I3CF+Hb8O3IBzVx3gU"
    "18WPYtTHj+Mt2svo/9Gb6fK20I//q5cslqlsLVus2CW74rxVy265rHyb3Qa7xe6wOyB8N7A4Zo+T"
    "4YQNLM+BP+GNchhySI7IEchhOSpHIcfkyNMYbUT/2mN0xE/jSHvvdNTxVr/TXtTxXkeaD4InfIgP"
    "gQ/yYT4MwiNLGst6US9rLOkVMqwSLgZKKPFNWkzZCTtl8cdO2j/Om7Z2GgRn7AzImbWzIDyXvYXs"
    "7Ww2exvZW9k72TvOu2uH3OsftsPu9Y/YERAeDW4iyAY3giyCW8HN4Jbzbr9P8IHKTSARXAouB5cR"
    "XAlkcAXBVfIKELCgMChEUBQUBEUIdgSFagZqmnL1B6iP6r36CPVBfVKfnPf5vcY7/UHXCNSKalEr"
    "UCPqyFBPOP8Q+cp8Vb4K+er8w3w18jX5qnAW4Vw4E84hnA9nw3nnLXQJvBCheCHwUnSJbB2ytdn6"
    "7D1k72bvZ+8j+yB7L/sAWZW9nx5CejA9nB5GeiQ9VCFQKZSwE7ApLdok/i7glFuzySqBaoq7andL"
    "VSK4j+Be8CB44B1Twf1ABcqBB8dVWoW0mqK22kVtTVrjvNpLFtJetJJ+rF4iYkaCow4XNM7ri2S4"
    "pC/oHS497CRDsb/DT/e7fLkvq72bOttxS9/S3m0CWX1b4w55m91W/B/aihmNLXqrPisgxBkhBMrE"
    "WVHmvHLBfoDF7Cf7CfaDdbNuEM4fsThsj5LRxjxiTeKZwS+JGTCDMIkZyl5H9lr2RvYGstezN7M3"
    "QTj70q3mKzK8Fi/FSYFT4oQ4JXBSnCbDGcKMGFcRK2BFYDtYIdvhvJ3hCMLRcDgcRTgWjoRjzhtP"
    "e5H+SnvSX0h/p73pb+f1dTvinSdDT9wdX8ngcuYqGa5lrmSOK5yg5WUxPUVBXEA/iLen35B+Tb+n"
    "39dMxOPkpXEa/3/4g/72FNKT6en0NNJT6Zn0DAiftddhr9kb9gbsdXuzT6Ff/Vb9CgOqTw0oJIRD"
    "4DlCL/S8cA0B/FboU7/UgZiS7H7KrKUxZdaDsRWUgVZFdBvRrehOdAfR7ehudBeE7zUJNIsnolmg"
    "RTQJfhz8BA/4CfDj/CQ/6bxTlxPi/lcSOWCGYAbNsBmGGTIjZgSER6OriK5FV6JriK5G16PrzrvR"
    "lXgvkjAJB14keJl0JVbCXrKX7WXQlrpir4Dw1QaNRv1YN2rkdIPOaTwhnKZIx6lYTSBN00mzFmad"
    "WWPWwaw168165214l8H7TJRJ1iNZl2xINiBZn2xMNiLZlGy4KbysuCGyZdmyNVmRLb8pbol8jQu/"
    "2nytC7+6fB0I16cJ0sF0IB1EmqRD6ZDzhrXFMyoTzyw6qQhPC8yQEj4MKsGHEO5AWBTuDHcSCouj"
    "eleA6qJHrgDVS1qhQVJHA/Yu7B17z96DvWvvRzlXsBvDAS+kNQj7E+UNqOTBIFFtj0j3g0SxR2D1"
    "7DF7DPaINbAGEG60f1yum3ri6FWTMHNOWc6aeacs56IKRCqqjCoRVUQPo4eIqqJKPgI+Sil2FHyM"
    "jzwXCEUnJRN0iefC7HaEdI/ZA7Pb7BV1EC4x1UM8oiT1yHmPWSXYQ1bBHoJVsUpW5bxqcxrmlDmT"
    "ao+IcseEntCY1Kme1JgiLJchl+SKXKH0IJfzbcg/zbfmnyLfnm/LtzuvY9Bx5iEyDP9NyxghzL+B"
    "f+Xfd1oU2x222KLE7rR2GX+L0gqoKC3nG5FvyOfyOeQb80/yT5Bvyuf4NEgSzOQbkH+cb7yicVlf"
    "1WHihYO0rgN8wFWafp6AD/DB7Dlky7Pns+eRPZe9kL2A7MXs+a6MFxLxDLe8cNSzK8MrPK5KFa8s"
    "Vd5BxRWv2OO0927KVbhLOeuuxj19R4fa69LPdfisS3svyAuf8Wce7yQtpAN4x4mdBV7gecGaAMch"
    "XCehjKQ0ierFWGnvgVbPKujylFadBDqhnqtnTyyIURCrQDPxi0euUjwmQwO9EtEOUocdogPir5iC"
    "6CjTzT5a/Ca/xUer3+wH90Dp+64pheHmoDkIU2oO5euRf5Svq7WoszW2zqKeBPUep8N36xGLUVcK"
    "LcaoLIY9CHvDfNiL8FfYE/5y3u+gHEFZcC44h+B8UM4awXK0G3NgT1gje+K8pnwr8i35tiGBYTEo"
    "hgVGxJDIPkW2PduWbUf2KeX6jjWU+9uzlO19YBfV9F2gFfVpJWlN75Phgb6nVzUsVX6rvVVtO/5F"
    "/4v2/pWA1eMWqR2jOualqxN23MoCSCYLZSFkgSzqUV6vInpU0avwS/WoUouDpGMHfQz5iT/kY9Af"
    "9rM5ZJ8QcXqCbFM2tyuGH+8mw554V8xPgVLaaX4a/BQ/02nxnAL9ufXC1dB2Es9DE3J0oRlPUC5w"
    "jorSZ4FPpHi+CFJAn0n4LPhY9Of9RR9L/oIfVSGqpiCsdkFYE9U4r1a+gXwt37ISMJ8VMx8FPivZ"
    "KVAsdohigRKxU5QI+IT5uAtXUhfg43yCTzjZm84DC5ijC4uYR1IMUjAlSQmhhJ6SnjEpeaHxUnfp"
    "dAHpfLqYLiJdSJfSJRBevuXSX7bstrgtcIdS3x2Bu4TLLMqJiKavnPp5+TLBi+RV8t8a/4f4+f/R"
    "+G8qy/9Xe/9DeLM+InCUpJQClFeBCqASii48JLwssCKWRPrMCWedeF6yJsEgmTeEBIl3RuAsFdhP"
    "Ap/FRzHs9OYQtmpso6q/TWM71f3tzmO6JkZtXB3XxqiLa+JpjT96hgyzelpHCtGDqCIdc5VgNB1H"
    "OpamOwR2iiKRvYjsJYrqSy6q5W63zfbgo8YnomCfND7rjzqdQTqdzqazSGfSuXTOLdMsrwR/yCv4"
    "QyfZKi+6Ds0l2xvjV9wT/4rxO+6NP2j6oPf6AnAeF8lwCRfo8kgYexcxAZCMogtThPkXpwAoAAlR"
    "QvsKwt9KnHT3Ea5HuC7cEG4gFG4cUhimfB/EOE6SeNjHCO3VER+jtFuTMi+hYErKBwWBpGxILDpe"
    "vKB5KTjnB/lB8EO8lB8CP8wPJveQ/NW+oMpxrwwoh1OXHj9bSjqzWKOEJHSJE9G+DvsQ/g77w36E"
    "feHAiAvaUTKMiRExJjBOODQIv4Rfw68ITfiNIrbDf0aGTl/7nT6eE1YjUMNqVI1CjaixY0BAivSc"
    "I4HlejTGWDwSj8UYj0fjaosaW0WpB9WUeGYF5sSMmBOYF7OiWqNK15ChVlfrZpf9WmypD+4fJMMh"
    "v9QfVhiirxhxknZY8V0e9/nuA3SB7+J7+B7w3Xxvj9OoedviCEurMAdc/ttvOMwBU/pHY1pP6W6B"
    "PGnSeh+P/Dr/kY96/7GvgWfooAud0JQDKRuO2xOODB4XsxpztO3m3Mab158SfE4+Jp8TfEq+kHmG"
    "sBlQHkWAWqPWUESotTe152jtDS2PQh6Rx+QxyKOS9AMIH/+Q4GPynj6EPuJDIte5fsp6ud71Uzbw"
    "KrcHq+UB13ff3+qjjXJ6m4+nfqs/EXuTMRHBeDLGRDxFhj+E98XYH+8lLocDhDsd3aPY2410V7on"
    "3UMo3ZvuBeF9sgSyWPrSh9wlS+QuyN3SV057PxBqOxRT2xSD2q4KVIHzCsd9pP6Yn/rehD/up7su"
    "C0hxhQxXxWXRFuNp3BpHFxFdiC5FlxBdjGQkQfgyfwX+kr/mr8Ff8TdmFGaM2OAYzLgZlWcgT8uz"
    "8qwnXcftjF1y7dLlhy6NVGEVIAVKF6y3imzWybebtzK4nclmbmdwK3OHDHcJqzGocdp641B/2xvO"
    "mxCPHW1pWHQHBwtxiYVPFKLCQtlKMjwk/NCiivAbjbf6tX6rvTckSiNtb8Hetll7G/YWEbQ7zrt7"
    "VOCYOCL2uvKwL7bn8bdpewHWtW0vOsJ64YTFSdLCiURyKbmcXEbimPAVJFfJK0dSlpxLziEpT84n"
    "55FcSM7JQciEtPIQ5KAcZgVgjBXWua1fT4ZHuk4/0nhM+IHAfVJuDTEaSbI3xsjFDfFuH3v8Xf4e"
    "H3v93b565fqNL9Vr1298pZagFtWyWoZaUitqBYRXS1yJK479GLvikvihC7VKXaVRrR9qNQ31R83w"
    "N6CX9VZOQk7IKTkF+UdOhoWOzRaERY7NFl5J4B6I3QW7x+6we2D32V1zCMQvDpvDMEfMobsZ3KOX"
    "w2bB5tgMmwObZ7Ns3nkLapVegVoxm2D+MRvNPzCbzGaz2XlbzBpH3T2z38XpvsTCdWjyjxyPqw8/"
    "uxT0KfziUtBnNeHe9WR6BOlR0rdHnb491uRUQbO2fbC/bb/th+2zAxXaq9TEqZ5VajzUFTrdB4qD"
    "/WoSakJNqSn32JPmF8xv02t+u0ObPn4M/CgJm8AJm2ONoFLfQOkEv2yPPas8oc4oUSEqvLOK3knl"
    "b6APv+jCb/STYYCwPO66d4E84bp3x0td4uXiIBkOiVKRXEVyLblyyx0q3SbDneRWYk7BnDSn7XrY"
    "dXaD3QC73m60G0F4Ez8Avp+yPAc/wEvTPNJuEpk9SPNpb0+MXtKWshPyuXwmn0OGslOGzuta8rFM"
    "DGTZcZAVMqwSlmOQ43LU7sRfWl0MotUlna4V/1z8dlWuL5bbXWObvU7whor/mwSvk7dkiAjLwy6V"
    "HZJHXCo7HFxEcCG4FFxCcDGQJnWBPWEmYFIzaSZhpszEqvWIqxNnt5ZI+6p9+/9bYW/oWkOg/J14"
    "K+xNkHrN2qyLuZv8F3gv/81/g//ifbwPhPsnHOObtLzetU4f8Ufg9fxxLsYTiocnLiKaYutRurBr"
    "7CUXljLcgq5MuPmABbf7bYFFoWW20KKIsF1DWcWutWvdYq+RqVuRCTkBmcrJMwpn1Wl6t/RDVMhX"
    "jqO9lK8hX8k39Y40P7LBdQTXghvBDQTXg5u8G/wnz/M8eA/v5j3u5vOjCmNUpI7DO0GlMKA/cZJ4"
    "vzJQX9UX9ZWQ+qa+Oe97zh3OPqFkRBXxoVUboNarjWoj1Aa1SW1yR2IbP2XwOfMxwxjYdlYQbESw"
    "KdgQbHIHO/8E/zhvc1WM6vhhLFchrVxh1U6h1bAasGpWy2rB6si7CHaBXWKXwC4y4ssgfPmgO00t"
    "jSt8r9JXJcqv9FHhPyRDFWF238X5A/bAxbnKViNbla3J1iBbna3N1oJwHbNgqwV2XCAlwlAcoyTe"
    "Gat+/O09DED1q0QlnhokDTswACJ//WDlYGXsHDsHdp6VX3UnuFe0sqiwapUlYANskA2CJWyIDYHw"
    "MGsFa2MtrM2dCrWyp85rr3YnrzXxfzlW+p/alnirLsn71u1zW5JtRbaFBEebExyt845nLIiwE+Hz"
    "8Fn4HGFnSP84ryttcid8zWkz0qa0JW0B4VZjYVa/2q/WM6vfrLFh7IU/nsfh9/AHwjj8Gf5E+CPs"
    "zvleblej/8TP7UJud87P7UZuV27PnxjTVJgTeANEeRPvs8YXIp3mK4wx38w3mK/mu/kOwjFRU6rD"
    "e+QeV4f3yr0gvI8Ngx5+JMq6PszN6Jbrw2TNG3c++9a683/747XAG/FKvHGdq7diCvhDlLNVoE20"
    "CKO9r/qLNs/MM890ftVGm06Y5+ZZucU5W2ZPKJxUx9VJ1346pdIXSLvSl+lLd/DxYggYpptO+5H2"
    "pQPpgOt69IdDCAfD4XAY4VA4MuIOEUfjKcfFJ3XWleObmY9OAX0QZoC4kOn/ksjP7vz4k/zizo8/"
    "V7v9VEOGWr/ar/VRR/ibxXda4u8W32xszTLMklkxK7TyZtmseob+nVmJakGSqS6qQ1Qb1ZvYMz++"
    "xub7MeUFDwJ1VNW5TnZtPGMx+7fviznX97WYJ2xmYKbNrJmFmTFz2QS3kpuJyngPMmqL2srqXEul"
    "ltW76Hj0VXvf3EI9+6bxVX8nQ6y/6XQZpJlW0hWkq+lydN8JjnvRA0T3I5VvQb4533pe44I+p9M/"
    "7vBkOp12hycz8hvkV/ldfof8JmMZe/LHpVh+zz928ruB17kEVlurUUd0d5fGbqLiuzV26T36oMIh"
    "VaoOKRxWB1UP0Is8XVRlepAl1VZ2S9wU2XJky7LnRA7CHag9gWgSOdHkvOYHGU9l7mfUVrXVPWlG"
    "bSsHzqEM0T1323dV7FXE6rv6URGjMlZx9jKyMnslewXZq9nLcglyUS6LGvxtUtdC1Ig61gLWTJF3"
    "GewKk+EzL+zs0qEObrtm+Z3gDoLbwd3grusb33kKtKMN/6rxb6TY/00T+ncy/AfhcNz1S1PzFuaN"
    "iUwE89a8a3JTCE/irzG+xSZ+oKH0fd0MtJDGbgFaSWf3CvwSPeKXwG/RKw4rHKH1OeJW6CgZjhHe"
    "6wjRPjLs9/f6+Q4v396t83opxnK8GGcfuyPYhnAJ4WK4HC4jXAmXwhWQpF/2fezyS4hMYbfv+3If"
    "KAz3y/1u9GXfT6AbP+iid/CTLkI9eOV09WsyvNGv9IA7We+P049IP6Sf0k9IP6af089Iv6SfGEDE"
    "zpuNMRfPxHyfK+R7+X5XyPfJLZCbZUZmvMsZuUVufR5TZumM32TwNvM689adeEaZqAVRc9QalSMq"
    "i85F5xCVR+e5m7Ip9Q/4d512v0dGBPGu8N3+KdHFPkr8nf53d8wbk9Htf6eLbj+mSgX+g3f3CwyI"
    "PjEgkIh+kZCmLBsgeZlGSN+m79J3SN+nUfrePdC7vhj98e84eeCRpiR9+thHAwmmBh+NJJkanZfz"
    "+Wcnbz+xcbAxlrIUbJxNsAmwSZbyo+BH+DH7yxGzXvvbnYj2RZdBKuFKdMX1gi9/czMqX+PvdLvx"
    "tzhqRNQQ5eoFXOcx2AwqcluCLQg2B5kgg2BrsCVMEY6HE+EEwjScDCcRToUTEz4mSaWw32C/WB9b"
    "BlthS2yFyhNbZqvOs/sE9ou9lKbwUbwXs8AcZujCLOYRdax5p6P2tzrS5gjMUSK0Rx2hPXY5gyv0"
    "ms45uV9ObA13/46QELqXBOcdAzoXXHD9sIuizTXlWsVTuAGOcNWjXWaf29B1kMLVoMwLSEkG5ccF"
    "gaDshCgSKBQ7xFMn8NrJSFk/9aXrJ0iPH3Fa/miVj2qqxmqbU2RbZR6yW/aciHEyPh6fjHEqPhHb"
    "TbD/EFv8B3az3RRl8I52z9UERDKJaBJfv54sCixR/VsSWBTLotXFVhsZnlJ0sX5XcfvYgKu4/fec"
    "qrpPhgeZe5kFi78jLBZLdsEedwf19H1X3XHDlWkff/wZP7mE5GIi5bg76kt5v+us9ql3UJF6r967"
    "8693SQbJlmRrshXJtiSTbEOyPdmqFpxImVeLbqZhKVyDcG3ohWsRrgnXBVsRbKOXvc297O3Bducx"
    "9RnqE5GnL448fbYPYJW9bxXsA1JzFc6rvCZwXVwV1wVuiGvihvNuCt4C3sxbkxv4O8p1E4kb5sq6"
    "caCbZqNTIBtEs8ufLQYwHtVoDwZmTXLR6bRLohLiITH+hxDuWLrKedXhNMI/4Uw4g3A6nK1x41C1"
    "ZKhDDfE/xwR/jQHjGKULKcbAJ92QyoRthRs6M3th9ph9Zh/MXrNfbob8R27hh10P54jZBrPdbDXb"
    "YbYZZpjzCsLfrgnbd851585bswFmvdkYXHXHkdeCa+448nr4DeFX4iffHT/5lgZIj6XH0+NIT6RB"
    "esKdGh03406Ap6fc7jkdmxcwXeblY6c1G/QfYBpTlDlQTEnwlMVpe9JmHzrCV5mtcoTvYXLLLd1t"
    "tg5sLVvP1oOtYxvknJudmi1yBHsHGXbaIitfQHYRbX7paPMLswSzaJbDDMKtXZl9FvvtXuLkOGD3"
    "2a8CRnwTpcBBcBz1ccw/4ps/TjpMm2mYP2amx7VqeoUpAC1HoSmEKTBFpghmhylMrjstdYN5HlvD"
    "XKpd4+7NM1tAsjJzTuC8KBfnXYv2AhkuEp62mLF/rPoN9Ys4ah/cWdm8xoKe0wsai3peP4dHRBGh"
    "Z0dhR+yYHYMdt6NcgVeUKtbkut3NrBmsibWYXe64hBggmigPNvl44jf7Zqtntn3JmMyeGHvj3XH4"
    "0p3EvwhfIXwZvu50Y5DP4ykXP5P+Hx/T/pRv3rlhv8i8d8N+755oNOmctvfd7r73xbUriZp0wYTm"
    "xaSPCfqFCzEuxufjizEuxRfiS45gXCSekXYhDdMX/L2buvuQniVWnp5JhTchxkV6NnccuRO5IHcC"
    "uZO54+aL46OfDe32L+Zrh4bW7ToigVbmVFkdUE97eq+bT9kjzJR7GZNsM9g/bAvbAraZZVgGbCvb"
    "EjBQlBacdJMApyjPkxbuhWjA38mfRrjJH/XcTSJ1qtAdbHTZSvztwHR4tt0SSWDXwK6y66LaxVhN"
    "dN61ks5FF1wr6Xz6wVWjj77riO8SvjsI2mWzd5G9k73HzjtFc45dcELiYhi5eaC34Ts3D0QfggvE"
    "ekQLhOsCtrqU3NLqJhFa4myTa/43Z5td878l2OFO8HcGO90JfvFuiz30DXssdtM23Wuxj7A55gpC"
    "oH653dK7AixjFeGCO5dfDBcJhUvX3ZHuDTLczFzPLLru/BItKJ7pDv1Mo1NrveDS77wYda3dMTKM"
    "+6P+MR+Bf9QP3NYPSl45tf0yidoRPY06eDN4E2+ZcQVqmpKEIwybTJ9rV/Sbfpg+M2A3u+S/xW5x"
    "yT/DBCmrAlHg6goTttmNpLTYFriBV7UTqljtUMVQO0nplXgVPvk++8cNWG6Ws5Azck59BwnTOCgG"
    "LUhJUEL3FhTzGfBpPtvhQ1OR+u24WJ/gi+ALfIkvgS/yZT7mDhbHsxVu8qAyW4lsRfbhJQ2pL+pk"
    "LZI1ybpkHZK1yfpV37Ml1l/xbZFrQVDWcC2IIn4G/Cw/zc96XJQKfiYpQMKSwqTQzWYVRDcR3Yiy"
    "yT/u6HZzshnJP1RRtoBwRv2A+qli+R7yg3x3OsaZ+FT8OEZD/ChOrrkG3PXnrlkd+vIZ3Y/sTDa5"
    "X9+Yb3YHhi11rvdb69vH+Dvr1AD72Dbyd26KJ3pk8djWW8nciF9BVroThcsqgnqr3pkdMDspEe10"
    "iajYPoSttFW2Ctap+GrYGlvF+sB+s345AzktZ9VPqG71Q3W7282rvPN6ZLGbfi5Rf9zYyNTOGMXx"
    "jviZQKfQIncGubO507mzyBEO17kKud42uZf5pE+gX/wWtsZ9X62tdd9Xl/5E+iPtTruR/kzzqXEU"
    "9Gv6FalJv/XHGIj7YtIT9N29qtdlv55wsxvP3MKuuPC7zK46dn+NbQXbRrG9zcX29nQE6XA6mo66"
    "s5WRYC2CNcE6U+yevcSchDlhTp0ETuEEfin0UnQUurHjgjjsAgnsF+ELl/K6hmOMxEOx+eEmtmK7"
    "6tm/TSHzHKaTclroxGlXesz18wLz2aWjTyaAOWaOm+PuOwJVBFVIm3eH27xFbLu7RcZfur7yi6sC"
    "18QVkbqCO0FMGA+IEad1SGvT+pAh3B4WhAUIWViYbHcMhI3H3tjfFrqcdi3OGVYMtpOVhB8Rfgg/"
    "hZ8Qfgw/F/hgfqGftiN9mnakHUjbU80U2ANWwSrAFKsM1rhBW29GYFZMC3PCtfCOs6wbkrqZVW4U"
    "pyI9iLQ0PWTnQHJ0Pl+JfEX+YTjl2MNk2I3wZ5gP8wi7w57cQeRKc4dyh5A7nDuYO+xG1w8dswjs"
    "UZvb47oLe3N7kduT23fQ4pAttYfctMtBy7vAQ/6Cv3Ct9q5TwGmcpIteyRlaMqgCVbTk8tUiXVih"
    "nHTY4gj9cvQUUXvUdi2D65mrmXQVqU1Xsi2gtNjK8m7OsTt71U3MXAkHESbhUO6Iu7OjbBFsgXj1"
    "Etgi8eppsD9shs2ATbNZvhd8D9+XMMfwCuQGyPVyo9wIuUFukpscy9k47wT6go1aEbVEbVGby3Ot"
    "8z4W/Dl/l8u5vlXrXAtsrVoPtU5tsI9cRNbfzCBLyTV7zYnU6+dinI/LqfzhHBW/adf8mIHdDsvs"
    "NssI2QJb4LzCZI3LOl76xHV3cukXFwyfJ1yzalKktUhr0jq20032FKd9bmynn60lFsHWpT9cEMU2"
    "daV/IixGuDMsCUsQFoc+f+Lm/5ryTU7+P0nn3bnqXI4jd4DeYClyPHcwPemI1yn5x4X+VHLBceTz"
    "aZvbS63pU7eX2nKnXBE+nTuN3KncGbXWPe0a3uTG6JrZlJNOf9gfsCla2BGwUTbMRp26GunUeE4V"
    "5bmrKaEO/zjtM53uckc8fm6/u4l9uQPI7c9xtuB674uyy3WFX9gMqE5stVthM7RK424ObCy6geh6"
    "dFO5rp8qsdfcBNFVu82t4Na0FWlL2iY/uP9v4aP86PLrp5ea5O8LHbpzv7CkUKCIqo1d5/rVa+Un"
    "0H/3OdyKcFuYCbcR3wu3s0n3DBNszD3DeO6kIyCnWBmYYOW2EPSiisLt7hdYXqBHdIvcPnfze9Nh"
    "pEPpyP8Dj7B6/g=="
)

MAZE_4_BASE64 = (
    "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"
    "tdz/ARPQzxg="
)

def get_maze_id(level):
    """Map 0-indexed RAM level to maze ID 1-4 (2 levels per maze, cycles every 8)."""
    return (level // 2) % 4 + 1

def load_prebuilt_graph(b64_str):
    """Decompress base64 graph representation into adjacency set representation."""
    graph = defaultdict(set)
    if not b64_str:
        return graph
    compressed = base64.b64decode(b64_str.encode("utf-8"))
    decompressed = zlib.decompress(compressed)
    
    idx = 0
    while idx < len(decompressed):
        x = decompressed[idx]
        y = decompressed[idx+1]
        n_count = decompressed[idx+2]
        idx += 3
        
        node = (x, y)
        for _ in range(n_count):
            nx = decompressed[idx]
            ny = decompressed[idx+1]
            idx += 2
            graph[node].add((nx, ny))
            
    return graph

def is_in_house(x, y):
    """Check if Pacman or a ghost is inside the central ghost house."""
    return (75 <= x <= 101) and (72 <= y <= 88)

def get_neighbor_by_action(graph, px, py, action):
    """Get the coordinates of the neighbor node in the graph if taking a cardinal action."""
    for nx, ny in graph[(px, py)]:
        # Warp-around checks
        if action == 3: # LEFT
            if px > 140 and nx < 25:
                return (nx, ny)
            if nx < px - 2 and abs(ny - py) < 5:
                return (nx, ny)
        elif action == 2: # RIGHT
            if px < 25 and nx > 140:
                return (nx, ny)
            if nx > px + 2 and abs(ny - py) < 5:
                return (nx, ny)
        elif action == 1: # UP
            if ny < py - 2 and abs(nx - px) < 5:
                return (nx, ny)
        elif action == 4: # DOWN
            if ny > py + 2 and abs(nx - px) < 5:
                return (nx, ny)
    return None

def get_neighbor_fallback(px, py, action):
    """Estimate neighbor coordinate when it's not yet recorded in the graph."""
    if action == 1: return (px, py - 3) # UP
    if action == 2: return (px + 3, py) # RIGHT
    if action == 3: return (px - 3, py) # LEFT
    if action == 4: return (px, py + 3) # DOWN
    return None

def get_action_to_neighbor(px, py, nx, ny):
    """Find the action (1-4) that moves Pacman from (px, py) to neighbor (nx, ny)."""
    # Warp checks
    if px > 140 and nx < 25:
        return 3 # LEFT
    if px < 25 and nx > 140:
        return 2 # RIGHT
        
    # Cardinal checks
    if nx < px - 2 and abs(ny - py) < 5:
        return 3 # LEFT
    if nx > px + 2 and abs(ny - py) < 5:
        return 2 # RIGHT
    if ny < py - 2 and abs(nx - px) < 5:
        return 1 # UP
    if ny > py + 2 and abs(nx - px) < 5:
        return 4 # DOWN
    return 0

def get_ghost_valid_moves(graph, gx, gy, prev_gx, prev_gy):
    """Get valid ghost moves excluding 180-degree reversal if heading is known."""
    neighbors = graph[(gx, gy)]
    if prev_gx is None or prev_gy is None:
        return neighbors
    dx = gx - prev_gx
    dy = gy - prev_gy
    if dx == 0 and dy == 0:
        return neighbors
    valid = set()
    for nx, ny in neighbors:
        # Avoid reversal
        if (dx > 0 and nx < gx - 2) or (dx < 0 and nx > gx + 2) or (dy > 0 and ny < gy - 2) or (dy < 0 and ny > gy + 2):
            continue
        valid.add((nx, ny))
    return valid if valid else neighbors

def dijkstra_distance_map(graph, start, max_dist=None):
    """Compute shortest path distance in physical pixels from start to all reachable nodes."""
    start = (int(start[0]), int(start[1]))
    dist_map = {start: 0.0}
    if start not in graph:
        return dist_map
    queue = [(0.0, start)]
    while queue:
        d, curr = heapq.heappop(queue)
        if max_dist is not None and d > max_dist:
            break
        if d > dist_map[curr]:
            continue
        for neighbor in graph[curr]:
            weight = float(abs(curr[0] - neighbor[0]) + abs(curr[1] - neighbor[1]))
            if weight > 20: # Warp tunnel threshold
                weight = 4.0
            nd = d + weight
            if neighbor not in dist_map or nd < dist_map[neighbor]:
                dist_map[neighbor] = nd
                heapq.heappush(queue, (nd, neighbor))
    return dist_map

def get_dist_from_map(dist_map, target, start_pos):
    """Look up Dijkstra distance from map, fallback to Manhattan distance."""
    target = (int(target[0]), int(target[1]))
    if target in dist_map:
        return float(dist_map[target])
    return float(abs(start_pos[0] - target[0]) + abs(start_pos[1] - target[1]))

def dijkstra_distance(graph, start, target, max_dist=None):
    """Calculate shortest path distance in pixels, fallback to Manhattan."""
    start = (int(start[0]), int(start[1]))
    target = (int(target[0]), int(target[1]))
    if start == target:
        return 0.0
    if start not in graph or target not in graph:
        return float(abs(start[0] - target[0]) + abs(start[1] - target[1]))
    dist_map = {start: 0.0}
    queue = [(0.0, start)]
    while queue:
        d, curr = heapq.heappop(queue)
        if curr == target:
            return d
        if max_dist is not None and d > max_dist:
            break
        if d > dist_map[curr]:
            continue
        for neighbor in graph[curr]:
            weight = float(abs(curr[0] - neighbor[0]) + abs(curr[1] - neighbor[1]))
            if weight > 20:
                weight = 4.0
            nd = d + weight
            if neighbor not in dist_map or nd < dist_map[neighbor]:
                dist_map[neighbor] = nd
                heapq.heappush(queue, (nd, neighbor))
    return float(abs(start[0] - target[0]) + abs(start[1] - target[1]))

def dijkstra_from_pacman(graph, start):
    """
    Compute shortest path distance and first-step neighbor node using Dijkstra (pixel weights).
    Returns: { node: (distance, first_step_neighbor) }
    """
    start = (int(start[0]), int(start[1]))
    paths_map = {start: (0.0, start)}
    if start not in graph:
        return paths_map
    queue = [(0.0, start)]
    while queue:
        d, curr = heapq.heappop(queue)
        if d > paths_map[curr][0]:
            continue
        for neighbor in graph[curr]:
            weight = float(abs(curr[0] - neighbor[0]) + abs(curr[1] - neighbor[1]))
            if weight > 20:
                weight = 4.0
            nd = d + weight
            if neighbor not in paths_map or nd < paths_map[neighbor][0]:
                first_step = paths_map[curr][1] if curr != start else neighbor
                paths_map[neighbor] = (nd, first_step)
                heapq.heappush(queue, (nd, neighbor))
    return paths_map

def dijkstra_closest_target(paths_map, targets, start_pos):
    """Find the closest target in the set of targets using precomputed paths_map."""
    if not targets:
        return None, 9999.0, None
    reachable_targets = [t for t in targets if t in paths_map]
    if reachable_targets:
        closest = min(reachable_targets, key=lambda t: paths_map[t][0])
        dist, first_step = paths_map[closest]
        return closest, float(dist), first_step
    else:
        # Fallback to Manhattan distance
        best_t = min(targets, key=lambda t: abs(start_pos[0]-t[0]) + abs(start_pos[1]-t[1]))
        dist = float(abs(start_pos[0]-best_t[0]) + abs(start_pos[1]-best_t[1]))
        return best_t, dist, None

def init_pellets_and_energizers(graph, maze_id):
    """Initialize pellets and energizer coordinates based on the loaded maze graph."""
    remaining_energizers = {(18, 14), (18, 146), (158, 14), (158, 146)}
    remaining_pellets = set()
    for node in graph:
        x, y = node[0], node[1]
        in_house = (75 <= x <= 101) and (72 <= y <= 88)
        in_tunnel = (72 <= y <= 88) and (x < 25 or x > 140)
        if not in_house and not in_tunnel:
            remaining_pellets.add(node)
    return remaining_pellets, remaining_energizers

def update_dynamic_graph_and_targets(px, py, prev_p, level, graph, remaining_pellets, remaining_energizers, visited_nodes):
    """Dynamically update connectivity graph and track eaten pellets/energizers."""
    # Learn graph connectivity dynamically (just in case)
    new_nodes_discovered = []
    if prev_p is not None:
        ppx, ppy = int(prev_p[0]), int(prev_p[1])
        if (ppx, ppy) != (px, py):
            dist = abs(px - ppx) + abs(py - ppy)
            is_warp = (ppy == py) and ((ppx < 25 and px > 140) or (ppx > 140 and px < 25))
            if dist <= 15 or is_warp:
                if (px, py) not in graph:
                    new_nodes_discovered.append((px, py))
                if (ppx, ppy) not in graph:
                    new_nodes_discovered.append((ppx, ppy))
                graph[(ppx, ppy)].add((px, py))
                graph[(px, py)].add((ppx, ppy))
                
    # Maze 2+ dynamic pellet discovery
    if level >= 2:
        for node in new_nodes_discovered:
            x, y = node[0], node[1]
            in_house = (75 <= x <= 101) and (72 <= y <= 88)
            in_tunnel = (72 <= y <= 88) and (x < 25 or x > 140)
            if not in_house and not in_tunnel and node not in visited_nodes:
                remaining_pellets.add(node)
                
    visited_nodes.add((px, py))
    
    # Auto-connect warp tunnels dynamically
    for node in list(graph.keys()):
        if node[0] <= 20: # left entrance
            for rx in [158, 157, 156]:
                if (rx, node[1]) in graph:
                    graph[node].add((rx, node[1]))
                    graph[(rx, node[1])].add(node)
                    
    # Remove nodes close to Pacman from target sets
    for node in list(remaining_pellets):
        if abs(px - node[0]) + abs(py - node[1]) <= 3:
            remaining_pellets.discard(node)
            
    for node in list(remaining_energizers):
        if abs(px - node[0]) + abs(py - node[1]) <= 5:
            remaining_energizers.discard(node)

def extract_strategic_features(obs, graph, prev_p, remaining_pellets, remaining_energizers, visited_nodes, prev_ghosts_pos):
    """Extract a highly strategic 34-dimensional feature vector for macro actions."""
    px, py = int(obs[10]), int(obs[16])
    level = int(obs[123]) >> 4
    
    update_dynamic_graph_and_targets(px, py, prev_p, level, graph, remaining_pellets, remaining_energizers, visited_nodes)
    
    # Precompute distance maps
    pacman_paths = dijkstra_from_pacman(graph, (px, py))
    
    blue_timer = int(obs[116])
    ghosts_pos = []
    ghosts_in_house = []
    is_blue = []
    for i in range(4):
        gx = int(obs[6 + i])
        gy = int(obs[12 + i])
        ghosts_pos.append((gx, gy))
        in_h = is_in_house(gx, gy)
        ghosts_in_house.append(in_h)
        is_blue.append((blue_timer > 0) and not in_h)
        
    ghost_dist_maps = [dijkstra_distance_map(graph, g) for g in ghosts_pos]
    
    features = []
    
    # 1, 2: Normalized Pacman position
    features.append(px / 160.0)
    features.append(py / 160.0)
    
    # 3-6: Normalized ghost distances
    ghost_dists = []
    for i, g_pos in enumerate(ghosts_pos):
        d = get_dist_from_map(ghost_dist_maps[i], (px, py), g_pos)
        ghost_dists.append(d)
        features.append(min(d / 150.0, 1.0)) # Scaled by physical screen width
        
    # 7-14: Normalized ghost relative directions
    for i, g_pos in enumerate(ghosts_pos):
        dx = g_pos[0] - px
        dy = g_pos[1] - py
        dist = abs(dx) + abs(dy)
        if dist > 0:
            features.append(dx / dist)
            features.append(dy / dist)
        else:
            features.append(0.0)
            features.append(0.0)
            
    # 15: Distance to closest active non-blue ghost
    min_non_blue_dist = 9999.0
    for i, d in enumerate(ghost_dists):
        if not is_blue[i] and not ghosts_in_house[i]:
            if d < min_non_blue_dist:
                min_non_blue_dist = d
    features.append(min(min_non_blue_dist / 150.0, 1.0))
    
    # 16: Blue timer
    features.append(blue_timer / 255.0)
    
    # 17: Closest remaining pellet distance
    _, pellet_dist, _ = dijkstra_closest_target(pacman_paths, remaining_pellets, (px, py))
    features.append(min(pellet_dist / 150.0, 1.0))
    
    # 18: Closest remaining energizer distance
    _, energizer_dist, _ = dijkstra_closest_target(pacman_paths, remaining_energizers, (px, py))
    features.append(min(energizer_dist / 150.0, 1.0))
    
    # 19: Remaining energizers ratio
    features.append(len(remaining_energizers) / 4.0)
    
    # 20: Remaining pellets ratio
    features.append(min(len(remaining_pellets) / 1645.0, 1.0))
    
    # 21: Lives
    lives = int(obs[123]) & 0x0F
    features.append(lives / 5.0)
    
    # 22: Level
    features.append(level / 10.0)
    
    # 23-26: Direction safety (UP, RIGHT, LEFT, DOWN)
    for a in [1, 2, 3, 4]:
        neighbor = get_neighbor_by_action(graph, px, py, a)
        if neighbor is not None:
            min_g_d = 9999.0
            for i, g_pos in enumerate(ghosts_pos):
                if not is_blue[i] and not ghosts_in_house[i]:
                    d = get_dist_from_map(ghost_dist_maps[i], neighbor, g_pos)
                    if d < min_g_d:
                        min_g_d = d
            features.append(min(min_g_d / 150.0, 1.0))
        else:
            features.append(0.0)
            
    # 27: Is in dead end
    features.append(float(len(graph[(px, py)]) <= 1))
    
    # 28-31: Ghosts in house
    for in_h in ghosts_in_house:
        features.append(float(in_h))
        
    # 32: Pacman in house
    features.append(float(is_in_house(px, py)))
    
    # 33: Closest blue ghost distance
    min_blue_dist = 9999.0
    for i, d in enumerate(ghost_dists):
        if is_blue[i]:
            if d < min_blue_dist:
                min_blue_dist = d
    features.append(min(min_blue_dist / 150.0, 1.0))
    
    # 34: Number of active blue ghosts
    num_blue = sum(1 for b in is_blue if b)
    features.append(num_blue / 4.0)
    
    return np.array(features, dtype=np.float32), (px, py)

OPPOSITE_ACTIONS = {1: 4, 2: 3, 3: 2, 4: 1}

def heuristic_execute(strategy_id, obs, graph, remaining_pellets, remaining_energizers, prev_action=0):
    """Translate high level strategy to cardinal action (1-4) or fallback (0)."""
    px, py = int(obs[10]), int(obs[16])
    blue_timer = int(obs[116])
    
    ghosts_pos = []
    ghosts_in_house = []
    is_blue = []
    for i in range(4):
        gx = int(obs[6 + i])
        gy = int(obs[12 + i])
        ghosts_pos.append((gx, gy))
        in_h = is_in_house(gx, gy)
        ghosts_in_house.append(in_h)
        is_blue.append((blue_timer > 0) and not in_h)
        
    pacman_paths = dijkstra_from_pacman(graph, (px, py))
    
    def action_to_targets(targets):
        if not targets:
            return 0
        _, _, next_node = dijkstra_closest_target(pacman_paths, targets, (px, py))
        if next_node is not None:
            return get_action_to_neighbor(px, py, next_node[0], next_node[1])
        return 0

    if strategy_id == 0:  # Eat Pellet
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 1:  # Eat Energizer
        act = action_to_targets(remaining_energizers)
        if act != 0:
            return act
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 2:  # Escape (with direction momentum)
        best_a = 0
        max_safety = -9999.0
        ghost_dist_maps = [dijkstra_distance_map(graph, g) for g in ghosts_pos]
        for a in [1, 2, 3, 4]:
            neighbor = get_neighbor_by_action(graph, px, py, a)
            if neighbor is not None:
                min_g_dist = 9999.0
                for i, g_pos in enumerate(ghosts_pos):
                    if not is_blue[i] and not ghosts_in_house[i]:
                        d = get_dist_from_map(ghost_dist_maps[i], neighbor, g_pos)
                        if d < min_g_dist:
                            min_g_dist = d
                score = min_g_dist
                # Direction momentum bonus (expressed in equivalent pixels)
                if prev_action > 0:
                    if a == prev_action:
                        score += 5.0
                    elif a == OPPOSITE_ACTIONS.get(prev_action):
                        score -= 5.0
                if score > max_safety:
                    max_safety = score
                    best_a = a
        if best_a != 0:
            return best_a
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 3:  # Chase Blue (with timing guard)
        blue_ghosts = {ghosts_pos[i] for i in range(4) if is_blue[i]}
        if blue_ghosts:
            closest_bg, dist, next_node = dijkstra_closest_target(pacman_paths, blue_ghosts, (px, py))
            # Speed safety timer guard: blue_timer > dist_in_pixels * 1.25
            if closest_bg is not None and blue_timer > dist * 1.25:
                if next_node is not None:
                    return get_action_to_neighbor(px, py, next_node[0], next_node[1])
        return action_to_targets(remaining_pellets)
        
    elif strategy_id == 4:  # Wait/Lure
        closest_e, dist, next_node = dijkstra_closest_target(pacman_paths, remaining_energizers, (px, py))
        if closest_e is not None:
            if dist > 15.0: # pixel distance > 15
                if next_node is not None:
                    return get_action_to_neighbor(px, py, next_node[0], next_node[1])
            else:
                # Close to energizer
                min_ghost_dist = 9999.0
                ghost_dist_maps = [dijkstra_distance_map(graph, g) for g in ghosts_pos]
                for i, g_pos in enumerate(ghosts_pos):
                    if not is_blue[i] and not ghosts_in_house[i]:
                        d = get_dist_from_map(ghost_dist_maps[i], (px, py), g_pos)
                        if d < min_ghost_dist:
                            min_ghost_dist = d
                if min_ghost_dist <= 30.0: # ghost within 30 pixels
                    if next_node is not None:
                        return get_action_to_neighbor(px, py, next_node[0], next_node[1])
                else:
                    # Patrol/Wait: move away from energizer
                    for neighbor in graph[(px, py)]:
                        if neighbor != closest_e:
                            return get_action_to_neighbor(px, py, neighbor[0], neighbor[1])
                    if next_node is not None:
                        return get_action_to_neighbor(px, py, next_node[0], next_node[1])
        return action_to_targets(remaining_pellets)

    return 0

def check_action_safety(graph, px, py, action, ghosts_pos, prev_ghosts_pos, is_blue, ghosts_in_house):
    """Lookahead 3-step Safety Filter with Ghost Momentum prediction and Safety Margin (Pixel distance)."""
    P1 = get_neighbor_by_action(graph, px, py, action)
    active_ghost_indices = [i for i in range(4) if not is_blue[i] and not ghosts_in_house[i]]
    if not active_ghost_indices:
        return True
        
    # Manhattan safety fallback
    if P1 is None:
        P1_est = get_neighbor_fallback(px, py, action)
        if P1_est is None:
            return False
        for i in active_ghost_indices:
            g = ghosts_pos[i]
            if abs(P1_est[0] - g[0]) + abs(P1_est[1] - g[1]) <= 12.0:
                return False
        return True
        
    SAFETY_MARGIN = 12.0 # minimum buffer in pixels
    
    # Precompute ghost potential states (cx, cy, px, py) at t=0, 1, 2, 3 to prevent reversal
    ghost_states_t = {0: []}
    for i in range(4):
        g = ghosts_pos[i]
        pg = prev_ghosts_pos[i] if prev_ghosts_pos else None
        ghost_states_t[0].append({(int(g[0]), int(g[1]), int(pg[0]) if pg else None, int(pg[1]) if pg else None)})
        
    for t in [1, 2, 3]:
        states_t = []
        for i in range(4):
            curr_states = ghost_states_t[t-1][i]
            next_states = set()
            for cx, cy, p_gx, p_gy in curr_states:
                valid_moves = get_ghost_valid_moves(graph, cx, cy, p_gx, p_gy)
                for nx, ny in valid_moves:
                    next_states.add((nx, ny, cx, cy))
            states_t.append(next_states)
        ghost_states_t[t] = states_t
        
    # Check t=1 safety at P1
    for i in active_ghost_indices:
        for gx, gy, _, _ in ghost_states_t[1][i]:
            d = dijkstra_distance(graph, P1, (gx, gy), max_dist=SAFETY_MARGIN)
            if d <= SAFETY_MARGIN:
                return False
                
    # Helper to check if a node is safe at step t (t=2, 3)
    def is_node_safe(node, t):
        for i in active_ghost_indices:
            for gx, gy, _, _ in ghost_states_t[t][i]:
                d = dijkstra_distance(graph, node, (gx, gy), max_dist=SAFETY_MARGIN)
                if d <= SAFETY_MARGIN:
                    return False
        return True

    # Search for any safe path of length 3 (P1 -> P2 -> P3)
    for P2 in graph[P1]:
        if is_node_safe(P2, 2):
            for P3 in graph[P2]:
                if is_node_safe(P3, 3):
                    return True
                    
    return False
