class Timer:
    def __init__(self,timeout=1,est_rtt=0,dev_rtt=0):
        self.timeout = timeout
        self.start_timer = False
        self.est_rtt = est_rtt
        self.dev_rtt = dev_rtt 
        self.alpha = 0.125
        self.beta = 0.25
    
    def calc_est_rtt(self,sample_rtt):
        self.est_rtt = (1-self.alpha)*self.est_rtt + self.alpha*sample_rtt
    
    def calc_dev_rtt(self,sample_rtt):
        self.dev_rtt = (1-self.beta)*self.dev_rtt + self.beta*abs(sample_rtt-self.est_rtt)

    def calc_timeout(self,sample_rtt):
        self.calc_est_rtt(sample_rtt)
        self.dev_rtt(sample_rtt)
        self.timeout = self.est_rtt + 4*self.dev_rtt