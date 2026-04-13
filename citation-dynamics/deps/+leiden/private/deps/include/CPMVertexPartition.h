#ifndef CPMVERTEXPARTITION_H
#define CPMVERTEXPARTITION_H

#include <LinearResolutionParameterVertexPartition.h>

class CPMVertexPartition : public LinearResolutionParameterVertexPartition
{
  public:
     // with standardized
    CPMVertexPartition(Graph* graph,
                       double resolution_parameter,
                       double ha_shift, double ha_scale,
                       double hr_shift, double hr_scale);
    CPMVertexPartition(Graph* graph,
                       vector<size_t> const& membership,
                       double resolution_parameter,
                       double ha_shift, double ha_scale,
                       double hr_shift, double hr_scale);
    virtual ~CPMVertexPartition();
    virtual CPMVertexPartition* create(Graph* graph);
    virtual CPMVertexPartition* create(Graph* graph, vector<size_t> const& membership);

    virtual double diff_move(size_t v, size_t new_comm);
    virtual double quality(double resolution_parameter);

    double ha_shift;
    double ha_scale;
    double hr_shift;
    double hr_scale;

  protected:
  private:
};

#endif // CPMVERTEXPARTITION_H
