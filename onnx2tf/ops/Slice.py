import random
random.seed(0)
import numpy as np
np.random.seed(0)
import tensorflow as tf
from tensorflow.python.keras.layers import Lambda
import onnx_graphsurgeon as gs
from onnx2tf.utils.common_functions import (
    get_constant_or_variable,
    print_node_info,
)
from onnx2tf.utils.enums import NUMPY_DTYPES_TO_TF_DTYPES


@print_node_info
def make_node(
    *,
    graph_node: gs.Node,
    tf_layers_dict: dict,
    **kwargs: dict,
):
    """Slice

    Parameters
    ----------
    graph_node: gs.Node
        graph_surgeon Node

    tf_layers_dict: dict
        optype, shape, dtype, tensorflow graph
    """
    input_tensor = get_constant_or_variable(graph_node.inputs[0])
    input_tensor = tf_layers_dict[input_tensor.name]['tf_node'] \
        if isinstance(input_tensor, gs.Variable) else input_tensor

    starts = get_constant_or_variable(graph_node.inputs[1])
    starts = tf_layers_dict[starts.name]['tf_node'] \
        if isinstance(starts, gs.Variable) else starts
    if isinstance(starts, np.ndarray):
        starts = tf.constant(starts, dtype=NUMPY_DTYPES_TO_TF_DTYPES[starts.dtype])

    ends = get_constant_or_variable(graph_node.inputs[2])
    ends = tf_layers_dict[ends.name]['tf_node'] \
        if isinstance(ends, gs.Variable) else ends
    if isinstance(ends, np.ndarray):
        ends = tf.constant(ends, dtype=NUMPY_DTYPES_TO_TF_DTYPES[ends.dtype])

    input_tensor_shape = tf.shape(
        input=input_tensor,
        out_type=ends.dtype,
    )
    input_tensor_rank = tf.rank(input_tensor)

    axes = None
    if len(graph_node.inputs) >= 4:
        axes = get_constant_or_variable(graph_node.inputs[3])
    axes = tf_layers_dict[axes.name]['tf_node'] \
        if isinstance(axes, gs.Variable) else axes
    if isinstance(axes, np.ndarray):
        axes = tf.constant(axes, dtype=NUMPY_DTYPES_TO_TF_DTYPES[axes.dtype]) \
            if len(graph_node.inputs) >= 4 else tf.range(tf.shape(starts)[0], dtype=ends.dtype)
    else:
        axes = axes if len(graph_node.inputs) >= 4 else tf.range(tf.shape(starts)[0], dtype=ends.dtype)

    steps = None
    if len(graph_node.inputs) >= 5:
        steps = get_constant_or_variable(graph_node.inputs[4])
    steps = tf_layers_dict[steps.name]['tf_node'] \
        if isinstance(steps, gs.Variable) else steps
    if isinstance(steps, np.ndarray):
        steps = tf.constant(steps, dtype=NUMPY_DTYPES_TO_TF_DTYPES[steps.dtype])

    graph_node_output: gs.Variable = graph_node.outputs[0]
    shape = graph_node_output.shape
    dtype = graph_node_output.dtype



    # Preserving Graph Structure (Dict)
    tf_layers_dict[graph_node_output.name] = {
        'optype': graph_node.op,
        'shape': shape,
        'dtype': dtype,
    }

    # # Generation of TF OP
    # is_axes_negative = tf.less(
    #     axes,
    #     tf.zeros_like(axes),
    # )
    # axes = tf.where(
    #     is_axes_negative,
    #     # axes + tf.cast(tf.rank(input_tensor), axes.dtype),
    #     axes + tf.cast(input_tensor_rank, axes.dtype),
    #     axes,
    # )

    # # expand a dimension of 1 at the end
    # sparse_indices = tf.cast(
    #     tf.expand_dims(axes, -1),
    #     tf.int64,
    # )

    # # build the indexed dimension sizes as sparse_shape
    # sparse_shape = tf.gather_nd(
    #     params=input_tensor_shape,
    #     indices=sparse_indices,
    # )
    # sparse_shape = tf.cast(
    #     sparse_shape,
    #     ends.dtype,
    # )

    # # take care of starts, ends that are larger than the dim size.
    # starts_min = tf.minimum(
    #     starts,
    #     sparse_shape,
    # )
    # ends_min = tf.minimum(
    #     ends,
    #     sparse_shape,
    # )

    # # take care of starts, ends that are negative
    # is_starts_negative = tf.less(
    #     starts_min,
    #     tf.zeros_like(starts_min),
    # )
    # starts_final = tf.where(
    #     is_starts_negative,
    #     starts_min + sparse_shape,
    #     starts_min,
    # )
    # is_ends_negative = tf.less(
    #     ends_min,
    #     tf.zeros_like(ends_min),
    # )
    # ends_final = tf.where(
    #     is_ends_negative,
    #     ends_min + sparse_shape,
    #     ends_min,
    # )

    # # need to densify everything for the inputs to slice
    # # the output shape is the input_tensor rank
    # output_shape = tf.reshape(
    #     input_tensor_rank,
    #     [1],
    # )
    # output_shape = tf.cast(
    #     output_shape,
    #     tf.int64,
    # )

    # # create dense tensor, pad 0 as default begins
    # def create_sparse_tensor(sparse_indices, starts_final, output_shape):
    #     return tf.sparse.SparseTensor(sparse_indices, starts_final, output_shape)

    # sparse_tensor = Lambda(
    #     create_sparse_tensor,
    #     output_shape=output_shape,
    #     arguments={
    #         'starts_final': starts_final,
    #         'output_shape': output_shape,

    #     }
    # )(sparse_indices)

    # dense_begins = tf.sparse.to_dense(
    #     tf.sparse.SparseTensor(
    #         sparse_indices,
    #         starts_final,
    #         output_shape,
    #     )
    # )

    # # create dense tensor, pad -1 for next step
    # dense_ends = tf.sparse.SparseTensor(
    #     sparse_indices,
    #     ends_final,
    #     output_shape,
    # )
    # dense_ends = tf.sparse.to_dense(
    #     dense_ends,
    #     default_value=tf.constant(-1, dtype=dense_begins.dtype)
    # )
    # dense_ends = tf.where(
    #     tf.equal(dense_ends, tf.constant(-1, dtype=dense_begins.dtype)),
    #     input_tensor_shape,
    #     dense_ends,
    # )

    # # create dense tensor for steps if not already so
    # if len(graph_node.inputs) >= 5:
    #     dense_steps = tf.sparse.SparseTensor(
    #         sparse_indices,
    #         steps,
    #         output_shape
    #     )
    #     dense_steps = tf.sparse.to_dense(
    #         dense_steps,
    #         default_value=tf.constant(1, dtype=steps.dtype)
    #     )
    # else:
    #     dense_steps = tf.ones(tf.shape(input_tensor_shape), ends.dtype)

    # tf_layers_dict[graph_node_output.name]['tf_node'] = \
    #     tf.strided_slice(
    #         input_=input_tensor,
    #         begin=dense_begins,
    #         end=dense_ends,
    #         strides=dense_steps,
    #         name=graph_node.name,
    #     )

    tf_layers_dict[graph_node_output.name]['tf_node'] = \
        tf.strided_slice(
            input_=input_tensor,
            begin=starts,
            end=ends,
            strides=steps,
            name=graph_node.name,
        )