#ifndef BRTYPEIVERTEXPARTITION_H
#define BRTYPEIVERTEXPARTITION_H

#include "LinearResolutionParameterVertexPartition.h"

class BRTypeIVertexPartition : public LinearResolutionParameterVertexPartition
{
    public:
        BRTypeIVertexPartition(Graph* graph,
                               vector<size_t> const& membership, double resolution_parameter);
        BRTypeIVertexPartition(Graph* graph,
                               vector<size_t> const& membership);
        BRTypeIVertexPartition(Graph* graph,
                               double resolution_parameter);

        // with standardized
        BRTypeIVertexPartition(Graph* graph,
                               double resolution_parameter,
                               int psik, double psic,
                               double ha_shift, double ha_scale,
                               double hr_shift, double hr_scale);
        BRTypeIVertexPartition(Graph* graph,
                               vector<size_t> const& membership,
                               double resolution_parameter,
                               int psik, double psic,
                               double ha_shift, double ha_scale,
                               double hr_shift, double hr_scale);

        BRTypeIVertexPartition(Graph* graph);
        virtual ~BRTypeIVertexPartition();
        virtual BRTypeIVertexPartition* create(Graph* graph);
        virtual BRTypeIVertexPartition* create(Graph* graph, vector<size_t> const& membership);

        virtual double diff_move(size_t v, size_t new_comm);
        virtual double quality(double resolution_parameter);

        int psik;
        double psic;

        double ha_shift;
        double ha_scale;
        double hr_shift;
        double hr_scale;

    protected:
    private:
};

#endif // BRTYPEIVERTEXPARTITION_H
