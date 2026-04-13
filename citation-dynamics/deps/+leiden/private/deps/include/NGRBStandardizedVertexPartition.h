#ifndef NGRBSTANDARDIZEDVERTEXPARTITION_H
#define NGRBSTANDARDIZEDVERTEXPARTITION_H

#include "LinearResolutionParameterVertexPartition.h"

class NGRBStandardizedVertexPartition : public LinearResolutionParameterVertexPartition
{
  public:
    NGRBStandardizedVertexPartition(Graph* graph,
          vector<size_t> const& membership, double resolution_parameter);
    NGRBStandardizedVertexPartition(Graph* graph,
          vector<size_t> const& membership);
    NGRBStandardizedVertexPartition(Graph* graph,
      double resolution_parameter);

    // with standardized
    NGRBStandardizedVertexPartition(Graph* graph,
                                    double resolution_parameter,
                                    double ha_shift, double ha_scale,
                                    double hr_shift, double hr_scale);
    NGRBStandardizedVertexPartition(Graph* graph,
                                    vector<size_t> const& membership,
                                    double resolution_parameter,
                                    double ha_shift, double ha_scale,
                                    double hr_shift, double hr_scale);

    NGRBStandardizedVertexPartition(Graph* graph);
    virtual ~NGRBStandardizedVertexPartition();
    virtual NGRBStandardizedVertexPartition* create(Graph* graph);
    virtual NGRBStandardizedVertexPartition* create(Graph* graph, vector<size_t> const& membership);

    virtual double diff_move(size_t v, size_t new_comm);
    virtual double quality(double resolution_parameter);

    double ha_shift;
    double ha_scale;
    double hr_shift;
    double hr_scale;

  protected:
  private:
};

#endif // NGRBSTANDARDIZEDVERTEXPARTITION_H
