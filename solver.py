#!/usr/bin/python3
# -*- coding: utf-8 -*-

from collections import namedtuple
from gurobipy import *
import math
import re

Point = namedtuple("Point", ['x', 'y'])
Facility = namedtuple("Facility", ['index', 'setup_cost', 'capacity', 'location'])
Customer = namedtuple("Customer", ['index', 'demand', 'location'])

def output(obj,solution):
    output_data = '%.2f' % obj + ' ' + str(0) + '\n'
    output_data += ' '.join(map(str, solution))
    return output_data

def greedy(customers,facilities):
    solution = [-1]*len(customers)
    capacity_remaining = [f.capacity for f in facilities]

    facility_index = 0
    for customer in customers:
        if capacity_remaining[facility_index] >= customer.demand:
            solution[customer.index] = facility_index
            capacity_remaining[facility_index] -= customer.demand
        else:
            facility_index += 1
            assert capacity_remaining[facility_index] >= customer.demand
            solution[customer.index] = facility_index
            capacity_remaining[facility_index] -= customer.demand
    used = [0]*len(facilities)
    for facility_index in solution:
        used[facility_index] = 1

    # calculate the cost of the solution
    obj = sum([f.setup_cost*used[f.index] for f in facilities])
    for customer in customers:
        obj += length(customer.location, facilities[solution[customer.index]].location)
    # prepare the solution in the specified output format
    return output(obj,solution)

def gurobi(customers,facilities,facility_count,customer_count,end):
    try:
        # Create a new model
        m = Model("fp")
        m.setParam('TimeLimit',end)
        m.setParam('OutputFlag',False)
        # Create variables
        var_matriz = [[0 for _ in range(customer_count)] for _ in range(facility_count)]
        """
        Clientes->Columnas
        Almacenes->Filas
        """
        for row in range(len(var_matriz)):
            for colum in range(len(var_matriz[row])):
                var_matriz[row][colum] = m.addVar( vtype=GRB.BINARY , name ="x %i-%i"% (row,colum))
        facility_open = [0]*facility_count
        for i in range(facility_count):
            facility_open[i] = m.addVar(vtype=GRB.BINARY , name ="y"+str(i))
        m.update()
        # Add constraints
        for facility in range(facility_count):
            m.addConstr(quicksum([var_matriz[facility][customer] for customer in range(customer_count)]) <= facility_open[facility]*customer_count, "c1")
        for customer in range(customer_count):
           m.addConstr(quicksum([var_matriz[facility][customer] for facility in range(facility_count)]) == 1, "c1")
        for j in range(facility_count):
            m.addConstr(
                quicksum(var_matriz[j][i]*customers[i].demand for i in range(customer_count))<=facility_open[j]*facilities[j].capacity, "c2")
        # Set objective:
        m.setObjective((quicksum(var_matriz[facility][customer]*length(facilities[facility].location,customers[customer].location)
                                 for customer in range(customer_count) for facility in range(facility_count))
        + quicksum(facility_open[facility]*facilities[facility].setup_cost  for facility in range(facility_count)))
        ,GRB.MINIMIZE)

        # Optimize model
        m.optimize()
        solution = [-1]*len(customers)
        for v in m.getVars():
            if v.x > 0 and v.varName.find("y") == -1:
                pattern = re.compile("\d+")
                solution[int(pattern.findall(v.varName)[1])] = int(pattern.findall(v.varName)[0])
        return output(m.objVal,solution)
    except GurobiError as e:
        print("Errorcode " + str(e.errno) + ": " + str(e))
    except AttributeError:
        print("Encountered an attribute error")

def length(point1, point2):
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

def solve_it (input_data):
    method = "gb"
    end = 300 # 5 min
    lines = input_data.split("\n")
    parts = lines[0].split()
    facility_count = int(parts[0])
    customer_count = int(parts[1])
    
    facilities = []
    for i in range(1, facility_count+1):
        parts = lines[i].split()
        facilities.append(Facility(i-1, float(parts[0]), int(parts[1]), Point(float(parts[2]), float(parts[3])) ))
    customers = []
    for i in range(facility_count+1, facility_count+1+customer_count):
        parts = lines[i].split()
        customers.append(Customer(i-1-facility_count, int(parts[0]), Point(float(parts[1]), float(parts[2]))))
    if method == "gb":
        print("Gurobi Solution")
        return gurobi(customers,facilities,facility_count,customer_count,end)
    elif method == "gr":
        print("Greedy Solution")
        return greedy(customers,facilities)
    else:
        return "ERROR: Method not valid"
    
import sys

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        file_location = sys.argv[1].strip()
        with open(file_location, 'r') as input_data_file:
            input_data = input_data_file.read()
        print(solve_it(input_data))
    else:
        print('This test requires an input file or any method "gr" greedy or "gb" gurobi.  Please select one from the data directory. (i.e. python solver.py ./data/fl_16_2)')

