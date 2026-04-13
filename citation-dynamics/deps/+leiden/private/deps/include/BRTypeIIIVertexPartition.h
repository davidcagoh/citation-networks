#ifndef BRTYPEIIIVERTEXPARTITION_H
#define BRTYPEIIIVERTEXPARTITION_H

#include "LinearResolutionParameterVertexPartition.h"

class BRTypeIIIVertexPartition : public LinearResolutionParameterVertexPartition
{
    public:
        BRTypeIIIVertexPartition(Graph* graph,
                               vector<size_t> const& membership, double resolution_parameter);
        BRTypeIIIVertexPartition(Graph* graph,
                               vector<size_t> const& membership);
        BRTypeIIIVertexPartition(Graph* graph,
                               double resolution_parameter);

        // with standardized
        BRTypeIIIVertexPartition(Graph* graph,
                               double resolution_parameter,
                               int psik, double psic, double ka,
                               double ha_shift, double ha_scale,
                               double hr_shift, double hr_scale);
        BRTypeIIIVertexPartition(Graph* graph,
                               vector<size_t> const& membership,
                               double resolution_parameter,
                               int psik, double psic, double ka,
                               double ha_shift, double ha_scale,
                               double hr_shift, double hr_scale);

        BRTypeIIIVertexPartition(Graph* graph);
        virtual ~BRTypeIIIVertexPartition();
        virtual BRTypeIIIVertexPartition* create(Graph* graph);
        virtual BRTypeIIIVertexPartition* create(Graph* graph, vector<size_t> const& membership);

        virtual double diff_move(size_t v, size_t new_comm);
        virtual double quality(double resolution_parameter);

        int psik;
        double psic;
        double ka;
        double ha_shift;
        double ha_scale;
        double hr_shift;
        double hr_scale;

    protected:
    private:
};

#endif // BRTYPEIIIVERTEXPARTITION_H
