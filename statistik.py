import numpy as np

def protokoll_ping():
    p1 = 1.245107503 - 1.244836418
    p2 = 1.277366997 - 1.277235239
    p3 = 1.309014974 - 1.308396750
    rtts = [p1, p2, p3]
    #return np.mean(rtts)
    print(f"Durchschnittliche RTT beim Ping: {np.mean(rtts):.2f} ms")

def protokoll_rtts_docker():
    rtts = [11.05, 2.85, 2,64]
    #return np.mean(rtts)
    print(f"Durchschnittliche RTT: {np.mean(rtts):.2f} ms")


protokoll_ping()
protokoll_rtts_docker()