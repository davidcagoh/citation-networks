#ifndef BRTYPEIIVERTEXPARTITION_H
#define BRTYPEIIVERTEXPARTITION_H

#include "LinearResolutionParameterVertexPartition.h"

class BRTypeIIVertexPartition : public LinearResolutionParameterVertexPartition
{
  public:
    BRTypeIIVertexPartition(Graph* graph,
          vector<size_t> const& membership, double resolution_parameter);
    BRTypeIIVertexPartition(Graph* graph,
          vector<size_t> const& membership);
    BRTypeIIVertexPartition(Graph* graph,
      double resolution_parameter);

    // with standardized
    BRTypeIIVertexPartition(Graph* graph,
                                    double resolution_parameter,
                                    double ha_shift, double ha_scale,
                                    double hr_shift, double hr_scale);
    BRTypeIIVertexPartition(Graph* graph,
                                    vector<size_t> const& membership,
                                    double resolution_parameter,
                                    double ha_shift, double ha_scale,
                                    double hr_shift, double hr_scale);

    BRTypeIIVertexPartition(Graph* graph);
    virtual ~BRTypeIIVertexPartition();
    virtual BRTypeIIVertexPartition* create(Graph* graph);
    virtual BRTypeIIVertexPartition* create(Graph* graph, vector<size_t> const& membership);

    virtual double diff_move(size_t v, size_t new_comm);
    virtual double quality(double resolution_parameter);

    double ha_shift;
    double ha_scale;
    double hr_shift;
    double hr_scale;

  protected:
  private:
};

#endif // BRTYPEIIVERTEXPARTITION_H
