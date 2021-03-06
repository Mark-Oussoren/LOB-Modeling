import time
import random
import math
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from statistics import median

class KyleModel:

    def __init__(self, V_0 = 5, V_N = 5, SIGMA_G = 0.4, SIGMA_T = 0.2, SIGMA = 2, ERR = 0.05, N = 50, MAX_ITER = 100):
        """
        one MM, one Informed, many Noise
        :param V_0: security value initially
        :param V_N: ending value of security (true)
        :param SIGMA_G: volatlity of security guess at time N
        :param SIGMA_T: true variance of security at time 0
        :param SIGMA: variance of net order flow of noise traders
        :param ERR: error rate willing to allow for true vs numerically solved for SIGMA at time 0
        :param N: discretized time periods for multiperiod model
        :param MAX_ITER: max iterations allowed for getting SIGMA[0]
        """
        self.V_0      = float(V_0)
        self.SIGMA_G  = float(SIGMA_G)
        self.SIGMA_T  = float(SIGMA_T)
        self.SIGMA    = float(SIGMA)
        self.ERR      = float(ERR)
        self.N        = N
        self.MAX_ITER = MAX_ITER
        self.V_N      = np.random.normal(self.V_0, self.SIGMA_G, 1)
        self.one_period_price()
        self.multiperiod_price()


    def one_period_price(self):
        """
        one-time period model calculates expected price MM sets after
        seeing the LOB (informed order + noise orders), this is just a conditional
        expectation and simplifies nicely to the formula below for MM_price &
        informed trader profit after time period
        :return: MM price + expected trader profit
        """
        ALPHA = self.V_0 * (self.SIGMA / math.sqrt(self.SIGMA_G))
        BETA = self.SIGMA / math.sqrt(self.SIGMA_G)
        MU = self.V_0
        LAMBDA = math.sqrt(self.SIGMA_G) / (2 * self.SIGMA)
        informed_order = (BETA * self.V_N) + ALPHA
        net_order = informed_order + np.random.normal(0, self.SIGMA, 1)
        mm_price = ((math.sqrt(self.SIGMA_G) / (2 * self.SIGMA)) * net_order) + self.V_0
        informed_profit = (((self.V_N - self.V_0) ** 2) * self.SIGMA) / (2 * math.sqrt(self.SIGMA_G))
        print(f'Market Maker Price: {mm_price}')
        print(f'Informed Trader Expected Profit: {informed_profit}')
        return {'MM Price': mm_price, 'Informed Profit': informed_profit}


    def multiperiod_price(self):
        """
        Solving the difference equations to find the optimal params and trader's expected profit as a function of time.
        :return: arrays of params that tell us trader position size, uninformed size, price change, volatility movement, and profit
        """
        dT = 1 / self.N
        MM_prices = np.zeros(self.N+1)
        ALPHA = np.zeros(self.N+1)
        BETA = np.zeros(self.N+1)
        DELTA = np.zeros(self.N+1)
        LAMBDA = np.zeros(self.N+1)
        SIGMA = np.zeros(self.N+1)
        price_changes = np.zeros(self.N+1)
        informed_orders = np.zeros(self.N+1)
        noise_orders = np.random.normal(0, (self.SIGMA ** 2) * (1 \ self.N), self.N+1)
        price_changes[0] = self.V_0
        informed_orders[0] = 0
        BETA[self.N] = 0
        DELTA[self.N] = 0
        SIGMA[self.N] = self.SIGMA_G
        LAMBDA[self.N] = math.sqrt(SIGMA[self.N]) / (self.SIGMA * math.sqrt(2 * dT))
        price_changes[self.N] = LAMBDA[self.N] * noise_orders[self.N]
        plt.ion()
        fig = plt.figure()
        plt.axis([0, 1000, 0, 1])
        iter = 0

        while (abs(SIGMA[0] - self.SIGMA_T) > self.ERR) and (iter < self.MAX_ITER):

            for n in range(self.N, 0, -1):

                ALPHA[n] = (LAMBDA[n] * (self.SIGMA ** 2)) / SIGMA[n]
                SIGMA[n-1] = SIGMA[n] / (1 - (ALPHA[n] * LAMBDA[n] * dT))
                BETA[n-1] = 1 / (4 * LAMBDA[n] * (1 - (BETA[n] * LAMBDA[n])))
                lambda_roots = np.roots([((self.SIGMA ** 2) * BETA[n] * dT) / SIGMA[n], -((self.SIGMA ** 2) * dT) / SIGMA[n], -BETA[n], 0.5])

                if len(lambda_roots) < 3:
                    LAMBDA[n-1] = max(lambda_roots)

                else:
                    LAMBDA[n-1] = np.median(lambda_roots)


                DELTA[n-1] = 1 / (4 * LAMBDA[n] * (1 - (BETA[n] * LAMBDA[n])))

            # plot convergence of the sigma (only plot one of the graphs each run - hence commented out)
            '''
            plt.scatter(iter, SIGMA[1] - self.SIGMA_T)
            plt.title('Convergence of Intial Volatility of V (SIGMA[0])')
            plt.xlabel('Iterations')
            plt.ylabel('SIGMA[0] - True Initial Vol')
            plt.show()
            plt.pause(0.0001)
            '''
            SIGMA[self.N] += -0.007
            iter += 1

        plt.clf()
        ALPHA[0] = (1 - (2 * BETA[0] * LAMBDA[0])) / (dT * ((2 * LAMBDA[0]) * (1 - (BETA[0] * LAMBDA[0]))))

        # functions for noise trader order & uninformed order sizes, price change, and future profit
        noise_cumulative = np.cumsum(noise_orders)
        for i in range(1, self.N):
            informed_orders[i] = (BETA[i] * (self.V_N - np.cumsum(price_changes[:i])[i-1])) / self.N
            price_changes[i+1] = LAMBDA[i+1] * (informed_orders[i] + noise_orders[i])

        plt.plot(np.arange(self.N+1), np.cumsum(informed_orders), label = 'Informed Orders')
        plt.plot(np.arange(self.N+1), np.cumsum(noise_orders), label = 'Noise Orders')
        plt.xlabel('Time')
        plt.ylabel('Order Size')
        plt.title('Order Sizes of Market Participants')
        plt.legend()
        plt.show()

        
if __name__ == "__main__":
    test = KyleModel()
