#ifndef __BINTREE_H__
#define __BINTREE_H__

typedef struct node {
    ADDRINT val;
    struct node *gt;
    struct node *lt;
} node_t;

node_t *bintree_init(ADDRINT val) {
    node_t *tree = (node_t *) malloc(sizeof(node_t));
    tree->val = val;
    tree->lt = NULL;
    tree->gt = NULL;
    return tree;
}

bool bintree_insert(node_t *tree, ADDRINT val) {
    node_t *senti = tree;
    if (senti->val == val)
        return false;
    else if (senti->val < val) {
        if (senti->gt) {
            return bintree_insert(senti->gt, val);
        } else {
            senti->gt = bintree_init(val);
            return true;
        }
    } else {
        if (senti->lt) {
            return bintree_insert(senti->lt, val);
        } else {
            senti->lt = bintree_init(val);
            return true;
        }
    }
    return false;
}

BOOL bintree_search_between(node_t *tree, ADDRINT min, ADDRINT max) {
    if (!tree)
        return false;
    node_t *senti = tree;
    if (min < senti->val && senti->val < max) {
        return true;
    }
    else if (senti->val < min)
        if (senti->gt)
            return bintree_search_between(senti->gt, min, max);
        else
            return false;
    else
        if (senti->lt)
            return bintree_search_between(senti->lt, min, max);
        else
            return false;
    return false;
}

BOOL bintree_search(node_t *tree, ADDRINT val) {
    if (!tree)
        return false;
    node_t *senti = tree;
    if (senti->val == val) {
        return true;
    }
    else if (senti->val < val)
        if (senti->gt)
            return bintree_search(senti->gt, val);
        else
            return false;
    else
        if (senti->lt)
            return bintree_search(senti->lt, val);
        else
            return false;
    return false;
}

void bintree_print(node_t *node, UINT64 lvl) {
    if (!node)
        return;
    string pad = "";
    for (unsigned int i = 0; i < lvl; i++)
        pad += " ";
    std::cerr << pad << std::hex << "[" << node->val << "]" << endl;
    std::cerr << pad << "[LT]" << endl;
    bintree_print(node->lt, lvl + 1);
    std::cerr << pad << "[GT]" << endl;
    bintree_print(node->gt, lvl + 1);
    return;
}

UINT64 depth(node_t *tree) {
    if (!tree)
        return 0;
    else 
        return 1 + MAX(depth(tree->gt), depth(tree->lt));
}

UINT64 nb_nodes(node_t *tree) {
    if (!tree)
        return 0;
    else 
        return 1 + nb_nodes(tree->gt) + nb_nodes(tree->lt);
}

VOID bintree_stats(node_t *node) {
    std::cerr << "NODES: " << nb_nodes(node) << endl;
    std::cerr << "DEPTH: " << depth(node) << endl;
    return;
}

#endif
