import math
import sys

from ortools.linear_solver import pywraplp

from models import Listing, Part, Store


def optimize(parts, listings, stores, shipping_costs):
    solver = pywraplp.Solver('lego_mip_optimization', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    infinity = solver.infinity()

    vars_part_listing = []
    vars_store = []

    # Variable - part listings
    for pi in range(len(parts)):
        for li in range(len(listings)):
            var = solver.IntVar(0.0, infinity, '{}-{}'.format(pi, li))
            vars_part_listing.append(var)

    # Variable - stores
    for si in range(len(stores)):
        var = solver.IntVar(0.0, 1.0, 'store-{}'.format(si))
        vars_store.append(var)

    print('Number of variables', solver.NumVariables())

    # Constraint - calculate the number of stores
    for si in range(len(stores)):
        for li in range(len(listings)):
            if listings[li].store_id != stores[si].store_id:
                continue
            sum = None
            for pi in range(len(parts)):
                index = to_var_index(parts, listings, pi, li)
                if sum is None:
                    sum = vars_part_listing[index]
                else:
                    sum += vars_part_listing[index]
            solver.Add(vars_store[si] >= sum * 0.0000001)

    # Constraint - minimum quantity for parts
    for pi, part in enumerate(parts):
        sum = None
        for li in range(len(listings)):
            index = to_var_index(parts, listings, pi, li)
            if sum is None:
                sum = vars_part_listing[index]
            else:
                sum += vars_part_listing[index]
        solver.Add(sum >= part.qty)

    # Constraint - listings are associated with corresponding parts
    for pi, part in enumerate(parts):
        for li, listing in enumerate(listings):
            if part.element_id != listing.element_id or part.color_id != listing.color_id:
                index = to_var_index(parts, listings, pi, li)
                solver.Add(vars_part_listing[index] == 0)

    # # Constraint - dont buy more than the max quantity of the vendor
    # for pi in range(len(parts)):
    #     for li, listing in enumerate(listings):
    #         if part.element_id != listing.element_id or part.color_id != listing.color_id:
    #             index = to_var_index(parts, listings, pi, li)
    #             solver.Add(vars[index] == 0)

    # Constraint - limited number of stores
    sum = None
    for si in range(len(stores)):
        if sum is None:
            sum = vars_store[si]
        else:
            sum += vars_store[si]
    solver.Add(sum <= 10)
    

    # Objective - minimize price
    sum = None
    for pi, part in enumerate(parts):
        for li, listing in enumerate(listings):
            index = to_var_index(parts, listings, pi, li)
            if not listing.price > 0:
                print('unrealistic price warning', listing.price)
            if sum is None:
                sum = vars_part_listing[index] * listing.price
            else:
                sum += vars_part_listing[index] * listing.price

    # # Objective - minimize stores
    # for si in range(len(stores)):
    #     if sum is None:
    #         sum = vars_store[si] * shipping_costs
    #     else:
    #         sum += vars_store[si] * shipping_costs

    solver.Minimize(sum)

    status = solver.Solve()

    optimal_listings = []
    if status == pywraplp.Solver.OPTIMAL:
        for pi in range(len(parts)):
            sys.stdout.write('{}'.format(parts[pi]))
            for li in range(len(listings)):
                solution = vars_part_listing[to_var_index(parts, listings, pi, li)].solution_value()
                if solution > 0:
                    sys.stdout.write(' {}'.format(listings[li]))
                    optimal_listings.append(listings[li])
            print('')
        # for si in range(len(stores)):
        #     print(stores[si].store_id, vars_store[si].solution_value())
        print('Solution:')
        print('Objective value =', solver.Objective().Value())
    else:
        print('The problem does not have an optimal solution.')
    
    return optimal_listings


def to_var_index(parts, listings, part_index, listing_index):
    return len(parts) * listing_index + part_index


def to_listing_index(parts, listings, var_index):
    return math.floor(var_index / len(parts))


def to_part_index(parts, listings, var_index):
    return var_index % len(parts)


if __name__ == '__main__':
    parts = [
        Part(3010,1,10),
        Part(3011,1,6),
    ]
    listings = [
        Listing(3010,1,10,0.1,'','', 's1', 301000),
        Listing(3011,1,10,0.1,'','', 's2', 301100)
    ]
    stores = [
        Store('s1'),
        Store('s2')
    ]
    optimize(parts, listings, stores)
