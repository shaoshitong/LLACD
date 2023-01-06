
_base_ = [
    '../../_base_/datasets/mmdet/coco_detection.py',
    '../../_base_/schedules/mmdet/schedule_2x.py',
    '../../_base_/mmdet_runtime.py'
]

# model settings
student = dict(
    type='mmdet.FasterRCNN',
    backbone=dict(
        type='ResNet',
        depth=50,
        num_stages=4,
        out_indices=(0, 1, 2, 3),
        frozen_stages=1,
        norm_cfg=dict(type='BN', requires_grad=True),
        norm_eval=True,
        style='pytorch',
        init_cfg=dict(type='Pretrained', checkpoint='torchvision://resnet50')),
    neck=dict(
        type='FPN',
        in_channels=[256, 512, 1024, 2048],
        out_channels=256,
        num_outs=5),
    rpn_head=dict(
        type='RPNHead',
        in_channels=256,
        feat_channels=256,
        anchor_generator=dict(
            type='AnchorGenerator',
            scales=[8],
            ratios=[0.5, 1.0, 2.0],
            strides=[4, 8, 16, 32, 64]),
        bbox_coder=dict(
            type='DeltaXYWHBBoxCoder',
            target_means=[.0, .0, .0, .0],
            target_stds=[1.0, 1.0, 1.0, 1.0]),
        loss_cls=dict(
            type='CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0),
        loss_bbox=dict(type='L1Loss', loss_weight=1.0)),
    roi_head=dict(
        type='StandardRoIHead',
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor',
            roi_layer=dict(type='RoIAlign', output_size=7, sampling_ratio=0),
            out_channels=256,
            featmap_strides=[4, 8, 16, 32]),
        bbox_head=dict(
            type='Shared2FCBBoxHead',
            in_channels=256,
            fc_out_channels=1024,
            roi_feat_size=7,
            num_classes=80,
            bbox_coder=dict(
                type='DeltaXYWHBBoxCoder',
                target_means=[0., 0., 0., 0.],
                target_stds=[0.1, 0.1, 0.2, 0.2]),
            reg_class_agnostic=False,
            loss_cls=dict(
                type='CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0),
            loss_bbox=dict(type='L1Loss', loss_weight=1.0))),
    # model training and testing settings
    train_cfg=dict(
        rpn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.7,
                neg_iou_thr=0.3,
                min_pos_iou=0.3,
                match_low_quality=True,
                ignore_iof_thr=-1),
            sampler=dict(
                type='RandomSampler',
                num=256,
                pos_fraction=0.5,
                neg_pos_ub=-1,
                add_gt_as_proposals=False),
            allowed_border=-1,
            pos_weight=-1,
            debug=False),
        rpn_proposal=dict(
            nms_pre=2000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.5,
                neg_iou_thr=0.5,
                min_pos_iou=0.5,
                match_low_quality=False,
                ignore_iof_thr=-1),
            sampler=dict(
                type='RandomSampler',
                num=512,
                pos_fraction=0.25,
                neg_pos_ub=-1,
                add_gt_as_proposals=True),
            pos_weight=-1,
            debug=False)),
    test_cfg=dict(
        rpn=dict(
            nms_pre=1000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            score_thr=0.05,
            nms=dict(type='nms', iou_threshold=0.5),
            max_per_img=100)
        # soft-nms is also supported for rcnn testing
        # e.g., nms=dict(type='soft_nms', iou_threshold=0.5, min_score=0.05)
    ))

teacher = dict(
    type='mmdet.CascadeRCNN',
    init_cfg=dict(type='Pretrained',
                  checkpoint='https://download.openmmlab.com/mmdetection/v2.0/cascade_rcnn/cascade_mask_rcnn_x101_64x4d_fpn_20e_coco/cascade_mask_rcnn_x101_64x4d_fpn_20e_coco_20200512_161033-bdb5126a.pth'),
    backbone=dict(
        type='ResNeXt',
        depth=101,
        groups=64,
        base_width=4,
        num_stages=4,
        out_indices=(0, 1, 2, 3),
        frozen_stages=1,
        norm_cfg=dict(type='BN', requires_grad=True),
        style='pytorch'),
    neck=dict(
        type='FPN',
        in_channels=[256, 512, 1024, 2048],
        out_channels=256,
        num_outs=5),
    rpn_head=dict(
        type='RPNHead',
        in_channels=256,
        feat_channels=256,
        anchor_generator=dict(
            type='AnchorGenerator',
            scales=[8],
            ratios=[0.5, 1.0, 2.0],
            strides=[4, 8, 16, 32, 64]),
        bbox_coder=dict(
            type='DeltaXYWHBBoxCoder',
            target_means=[.0, .0, .0, .0],
            target_stds=[1.0, 1.0, 1.0, 1.0]),
        loss_cls=dict(
            type='CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0),
        loss_bbox=dict(type='SmoothL1Loss', beta=1.0 / 9.0, loss_weight=1.0)),
    roi_head=dict(
        type='CascadeRoIHead',
        num_stages=1,
        stage_loss_weights=[1, 0.5, 0.25],
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor',
            roi_layer=dict(type='RoIAlign', output_size=7, sampling_ratio=0),
            out_channels=256,
            featmap_strides=[4, 8, 16, 32]),
        bbox_head=[
            dict(
                # NOTE: use `KDShared2FCBBoxHead` to discard loss computation
                type='KDShared2FCBBoxHead',
                in_channels=256,
                fc_out_channels=1024,
                roi_feat_size=7,
                num_classes=80,
                bbox_coder=dict(
                    type='DeltaXYWHBBoxCoder',
                    target_means=[0., 0., 0., 0.],
                    target_stds=[0.1, 0.1, 0.2, 0.2]),
                reg_class_agnostic=True,
                loss_cls=dict(
                    type='CrossEntropyLoss',
                    use_sigmoid=False,
                    loss_weight=1.0),
                loss_bbox=dict(type='SmoothL1Loss', beta=1.0,
                               loss_weight=1.0)),
            # dict(
            #     type='Shared2FCBBoxHead',
            #     in_channels=256,
            #     fc_out_channels=1024,
            #     roi_feat_size=7,
            #     num_classes=80,
            #     bbox_coder=dict(
            #         type='DeltaXYWHBBoxCoder',
            #         target_means=[0., 0., 0., 0.],
            #         target_stds=[0.05, 0.05, 0.1, 0.1]),
            #     reg_class_agnostic=True,
            #     loss_cls=dict(
            #         type='CrossEntropyLoss',
            #         use_sigmoid=False,
            #         loss_weight=1.0),
            #     loss_bbox=dict(type='SmoothL1Loss', beta=1.0,
            #                    loss_weight=1.0)),
            # dict(
            #     type='Shared2FCBBoxHead',
            #     in_channels=256,
            #     fc_out_channels=1024,
            #     roi_feat_size=7,
            #     num_classes=80,
            #     bbox_coder=dict(
            #         type='DeltaXYWHBBoxCoder',
            #         target_means=[0., 0., 0., 0.],
            #         target_stds=[0.033, 0.033, 0.067, 0.067]),
            #     reg_class_agnostic=True,
            #     loss_cls=dict(
            #         type='CrossEntropyLoss',
            #         use_sigmoid=False,
            #         loss_weight=1.0),
            #     loss_bbox=dict(type='SmoothL1Loss', beta=1.0, loss_weight=1.0))
        ],
        # mask_roi_extractor=dict(
        #     type='SingleRoIExtractor',
        #     roi_layer=dict(type='RoIAlign', output_size=14, sampling_ratio=0),
        #     out_channels=256,
        #     featmap_strides=[4, 8, 16, 32]),
        # mask_head=dict(
        #     type='FCNMaskHead',
        #     num_convs=4,
        #     in_channels=256,
        #     conv_out_channels=256,
        #     num_classes=80,
        #     loss_mask=dict(
        #         type='CrossEntropyLoss', use_mask=True, loss_weight=1.0))),
    ),
    # model training and testing settings
    train_cfg=dict(
        rpn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.7,
                neg_iou_thr=0.3,
                min_pos_iou=0.3,
                match_low_quality=True,
                ignore_iof_thr=-1),
            sampler=dict(
                type='RandomSampler',
                num=256,
                pos_fraction=0.5,
                neg_pos_ub=-1,
                add_gt_as_proposals=False),
            allowed_border=0,
            pos_weight=-1,
            debug=False),
        rpn_proposal=dict(
            nms_pre=2000,
            max_per_img=2000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=[
            dict(
                assigner=dict(
                    type='MaxIoUAssigner',
                    pos_iou_thr=0.5,
                    neg_iou_thr=0.5,
                    min_pos_iou=0.5,
                    match_low_quality=False,
                    ignore_iof_thr=-1),
                sampler=dict(
                    type='RandomSampler',
                    num=512,
                    pos_fraction=0.25,
                    neg_pos_ub=-1,
                    add_gt_as_proposals=True),
                pos_weight=-1,
                debug=False),
            # dict(
            #     assigner=dict(
            #         type='MaxIoUAssigner',
            #         pos_iou_thr=0.6,
            #         neg_iou_thr=0.6,
            #         min_pos_iou=0.6,
            #         match_low_quality=False,
            #         ignore_iof_thr=-1),
            #     sampler=dict(
            #         type='RandomSampler',
            #         num=512,
            #         pos_fraction=0.25,
            #         neg_pos_ub=-1,
            #         add_gt_as_proposals=True),
            #     pos_weight=-1,
            #     debug=False),
            # dict(
            #     assigner=dict(
            #         type='MaxIoUAssigner',
            #         pos_iou_thr=0.7,
            #         neg_iou_thr=0.7,
            #         min_pos_iou=0.7,
            #         match_low_quality=False,
            #         ignore_iof_thr=-1),
            #     sampler=dict(
            #         type='RandomSampler',
            #         num=512,
            #         pos_fraction=0.25,
            #         neg_pos_ub=-1,
            #         add_gt_as_proposals=True),
            #     pos_weight=-1,
            #     debug=False)
        ]),
    test_cfg=dict(
        rpn=dict(
            nms_pre=1000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            score_thr=0.05,
            nms=dict(type='nms', iou_threshold=0.5),
            max_per_img=100,
        )))


custom_imports = dict(imports=['JDA'], allow_failed_imports=False)
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)
jda_prob = 0.15
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='Resize', img_scale=(1333, 800), keep_ratio=True),
    dict(type='RandomFlip', flip_ratio=0.5),
    dict(type="ConcatWithAugmentation",
         ori_translate=[
             dict(type='Normalize', **img_norm_cfg),
             dict(type='Pad', size_divisor=32),
             # dict(type='DefaultFormatBundle'),
         ],
         aug_translate=[
             dict(type="BernoulliChoose",
                  translate=dict(type='Translate', prob=1, level=4, direction='vertical',max_translate_offset=150),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type="EqualizeTransform", prob=1.),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type='Translate', prob=1, level=2, direction='horizontal',max_translate_offset=150),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type='Shear', prob=1, level=2, direction='vertical'),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type='Rotate', prob=1., level=10, max_rotate_angle=30),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type="ColorTransform", level=6, prob=1.),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type="BrightnessTransform", level=3, prob=1.),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type="ContrastTransform", level=3, prob=1.),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type="InvertTransform", prob=1.),
                  p=jda_prob),
             dict(type="BernoulliChoose",
                  translate=dict(type='Shear', prob=1, level=1, direction='horizontal'),
                  p=jda_prob),
             dict(type='Normalize', **img_norm_cfg),
             dict(type='Pad', size_divisor=32),
             # dict(type='DefaultFormatBundle'),
         ]),

    dict(type='AugCollect', defaultformatbundle=dict(type='DefaultFormatBundle')
         , keys=['img', 'gt_bboxes', 'gt_labels']),
]
data = dict(train=dict(pipeline=train_pipeline))
# algorithm setting
algorithm = dict(
    type='JDADistill',
    collect_key=['img', 'gt_bboxes', 'gt_labels'],
    architecture=dict(
        type='MMDetArchitecture',
        model=student,
    ),
    distiller=dict(
        type='SingleTeacherDistiller',
        teacher=teacher,
        teacher_trainable=False,
        components=[
            dict(
                student_module='roi_head.bbox_head.fc_cls',
                teacher_module='roi_head.bbox_head.0.fc_cls',
                modules_with_student_inputs=[
                    dict(
                        student_module='roi_head.bbox_roi_extractor',
                        teacher_module='roi_head.bbox_roi_extractor.0',
                        same_indices=[1], )
                ],
                losses=[
                    dict(
                        type='CCD',
                        name='loss_dist_roi_cls_head',
                        temperature=1,
                    )
                ]),
        ]),
)

find_unused_parameters = True
fp16 = dict(loss_scale=512.)
# optimizer = dict(type='SGD', lr=0.04, momentum=0.9, weight_decay=0.0001)