#ifndef LEIDEN_H_
#define LEIDEN_H_

#include <iostream>
#include <string.h>
#include <cstring>

extern "C" {

size_t const* do_leiden( double       * const quality,
                         size_t const * const ij,
                         double const * const weights,
                         size_t       * const membership,
                         size_t const nv,
                         size_t const ne,
                         char const * const str_measure, double gamma,
                         int const seed,
                         int const is_directed,     // 0:undirected  1:directed
                         double const max_improv_input,
                         int const psik, double const psic, double const ka,
                         double const ha_shift, double const ha_scale,
                         double const hr_shift, double const hr_scale,
                         int const n_iter, int const n_piter, int const n_oiter );

double cpp_quality_leiden( size_t const * const ij,
                           double const * const weightsFromC,
                           size_t       * const membershipFromC,
                           size_t const nv,
                           size_t const ne,
                           char const * const str_measure, double gamma,
                           int const is_directed,
                           int const psik, double const psic, double const ka,
                           double const ha_shift, double const ha_scale,
                           double const hr_shift, double const hr_scale);

double cpp_move_leiden( size_t const * const ij,
                        double const * const weightsFromC,
                        size_t       * const membershipFromC,
                        size_t const nv,
                        size_t const ne,
                        char const * const str_measure, double gamma,
                        int const is_directed,
                        int const u,
                        int const icomm,
                        int const psik, double const psic, double const ka,
                        double const ha_shift, double const ha_scale,
                        double const hr_shift, double const hr_scale);

}

#endif // LEIDEN_H_
