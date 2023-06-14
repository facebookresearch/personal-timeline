// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.

// This source code is licensed under the license found in the
// LICENSE file in the root directory of this source tree.
const prod = {
    API_URL: 'http://localhost:8085'
};

const dev = {
    API_URL: 'http://localhost:8085'
};

export const config = process.env.NODE_ENV === 'development' ? dev : prod;
