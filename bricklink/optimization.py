import math
import sys

from ortools.linear_solver import pywraplp

from models import Listing, Part, Store


def optimize(parts, listings, stores):
    solver = pywraplp.Solver('lego_mip_optimization', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    infinity = solver.infinity()

    vars_part_listing = []
    vars_store = []

    # Variables - part listings
    for pi in range(len(parts)):
        for li in range(len(listings)):
            var = solver.IntVar(0.0, infinity, '{}-{}'.format(pi, li))
            vars_part_listing.append(var)

    # Variables - stores
    for si in range(len(stores)):
        var = solver.IntVar(0.0, 1.0, 'store-{}'.format(si))
        vars_store.append(var)

    print('Number of variables', solver.NumVariables())

    # Constraints - calculate the number of stores
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

    # Constraints - minimum quantity
    for pi, part in enumerate(parts):
        sum = None
        for li in range(len(listings)):
            index = to_var_index(parts, listings, pi, li)
            if sum is None:
                sum = vars_part_listing[index]
            else:
                sum += vars_part_listing[index]
        solver.Add(sum >= part.qty)

    # Constraints - listings are associated with corresponding parts
    for pi, part in enumerate(parts):
        for li, listing in enumerate(listings):
            if part.element_id != listing.element_id or part.color_id != listing.color_id:
                index = to_var_index(parts, listings, pi, li)
                solver.Add(vars_part_listing[index] == 0)

    # # Constraints - dont buy more than the max quantity of the vendor
    # for pi in range(len(parts)):
    #     for li, listing in enumerate(listings):
    #         if part.element_id != listing.element_id or part.color_id != listing.color_id:
    #             index = to_var_index(parts, listings, pi, li)
    #             solver.Add(vars[index] == 0)

    # # Objective - minimize price
    # sum = None
    # for part in parts:
    #     for listing in listings:
    #         index = to_var_index(parts, listings, pi, li)
    #         if sum is None:
    #             sum = vars_part_listing[index] * listing.price
    #         else:
    #             sum += vars_part_listing[index] * listing.price
    # solver.Minimize(sum)

    # Objective - minimize stores
    sum = None
    for si in range(len(stores)):
        if sum is None:
            sum = vars_store[si]
        else:
            sum += vars_store[si]
    solver.Minimize(sum)

    status = solver.Solve()

    optimal_listings = []
    if status == pywraplp.Solver.OPTIMAL:
        print('Solution:')
        print('Objective value =', solver.Objective().Value())
        for pi in range(len(parts)):
            for li in range(len(listings)):
                sys.stdout.write('{} '.format(vars_part_listing[to_var_index(parts, listings, pi, li)].solution_value()))
                optimal_listings.append(listings[li])
            print('')
        for si in range(len(stores)):
            print(stores[si].store_id, vars_store[si].solution_value())
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
        Listing(3010,1,10,0.1,'','', 's1'),
        Listing(3011,1,10,0.1,'','', 's2')
    ]
    stores = [
        Store('s1'),
        Store('s2')
    ]
    optimize(parts, listings, stores)
